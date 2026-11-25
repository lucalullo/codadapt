"""Read-only publication gates for the two manually invoked release workflows.

No upload occurs here. Registry writes are confined to the separate OIDC jobs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPO = "lucalullo/codadapt"
OWNER = "lucalullo"
VERSION = "2.2.0"
FILES = ("codadapt-2.2.0-py3-none-any.whl", "codadapt-2.2.0.tar.gz")
INDEXES = {"testpypi": "https://test.pypi.org", "pypi": "https://pypi.org"}
CDNS = {"testpypi": {"test-files.pythonhosted.org"}, "pypi": {"files.pythonhosted.org"}}
LIMIT = 64 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Unexpected network redirect")


def get(url, hosts, *, token=None, absent=False, limit=LIMIT):
    parsed = urlsplit(url)
    require(parsed.scheme == "https" and parsed.hostname in hosts and
            parsed.username is None and parsed.password is None and
            parsed.port in (None, 443), "Unexpected request origin")
    headers = {"User-Agent": "codadapt-release-verifier/2.2.0", "Cache-Control": "no-cache"}
    if token is not None:
        require(parsed.hostname == "api.github.com", "GitHub token must stay at GitHub")
        headers.update({"Authorization": "Bearer " + token,
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with build_opener(NoRedirect()).open(Request(url, headers=headers), timeout=45) as response:
            data = response.read(limit + 1)
    except HTTPError as exc:
        if absent and exc.code == 404:
            return None
        raise
    require(len(data) <= limit, "Response exceeded allowed size")
    return data


def gh(path):
    token = os.environ.get("GH_TOKEN")
    require(bool(token), "Read-only GitHub token required in the verification job")
    return json.loads(get("https://api.github.com" + path, {"api.github.com"}, token=token))


def validate_environment(doc, channel):
    require(doc.get("name") == channel, "Existing GitHub environment required: " + channel)
    if channel == "pypi":
        rules = [rule for rule in doc.get("protection_rules", []) if rule.get("type") == "required_reviewers"]
        require(len(rules) == 1, "Configure the existing pypi environment to require owner review")
        reviewers = rules[0].get("reviewers", [])
        require(len(reviewers) == 1 and reviewers[0].get("type") == "User" and
                reviewers[0].get("reviewer", {}).get("login") == OWNER,
                "The original pypi protection requires the owner as sole reviewer")
        require(doc.get("can_admins_bypass") is False, "Disable bypass of pypi protection rules")
        require(rules[0].get("prevent_self_review") is False,
                "The existing owner-only approval contract requires owner self-review")


def gate(channel):
    e = os.environ
    require(e.get("GITHUB_EVENT_NAME") == "workflow_dispatch", "Manual dispatch only")
    require(e.get("GITHUB_REPOSITORY") == REPO and e.get("GITHUB_REF") == "refs/heads/main", "Wrong repository or branch")
    require(e.get("GITHUB_ACTOR") == OWNER and e.get("GITHUB_TRIGGERING_ACTOR") == OWNER, "Owner-operated publication only")
    require(e.get("GITHUB_WORKFLOW_REF") == f"{REPO}/.github/workflows/publish-{channel}.yml@refs/heads/main", "Wrong workflow")
    require(e.get("PUBLISH_CONFIRMED") == "true", "Explicit publish selection required")
    require(e.get("TRUSTED_PUBLISHER_CONFIRMED") == "true", "Confirm the existing Trusted Publisher first")
    phrase = ("TEST" if channel == "testpypi" else "PUBLISH") + f" codadapt {VERSION}"
    require(e.get("OWNER_APPROVAL") == phrase, "Enter the exact approval phrase: " + phrase)
    validate_environment(gh(f"/repos/{REPO}/environments/{channel}"), channel)
    print("PASS_MANUAL_OWNER_AND_ENVIRONMENT_GATE")


def validate_test_run(doc, run_id, sha):
    require(str(doc.get("id")) == run_id and doc.get("status") == "completed" and
            doc.get("conclusion") == "success", "Require a completed successful TestPyPI run")
    require(doc.get("event") == "workflow_dispatch" and
            doc.get("path") == ".github/workflows/publish-testpypi.yml", "Wrong workflow/event")
    require(doc.get("head_sha") == sha and doc.get("head_branch") == "main", "TestPyPI must use the exact current source commit")
    require(doc.get("repository", {}).get("full_name") == REPO and
            doc.get("head_repository", {}).get("full_name") == REPO, "Foreign workflow run")
    require(doc.get("actor", {}).get("login") == OWNER and
            doc.get("triggering_actor", {}).get("login") == OWNER, "TestPyPI run must be owner-operated")
    require(type(doc.get("run_attempt")) is int and doc["run_attempt"] > 0, "Missing run attempt")


def verify_test_run(run_id):
    require(bool(re.fullmatch(r"[1-9][0-9]*", run_id or "")), "Enter the numeric successful TestPyPI run ID")
    doc = gh(f"/repos/{REPO}/actions/runs/{run_id}")
    sha = os.environ.get("GITHUB_SHA", "")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", sha)), "Missing source commit")
    validate_test_run(doc, run_id, sha)
    jobs = gh(f"/repos/{REPO}/actions/runs/{run_id}/attempts/{doc['run_attempt']}/jobs?per_page=100")
    require(jobs.get("total_count", 101) <= 100, "Unexpected TestPyPI job count")
    for name in ("Publish verified distributions to TestPyPI", "Verify published TestPyPI distributions"):
        matched = [job for job in jobs["jobs"] if job.get("name") == name]
        require(len(matched) == 1 and matched[0].get("conclusion") == "success", "Missing successful job: " + name)
    artifacts = gh(f"/repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100")
    require(artifacts.get("total_count", 101) <= 100, "Unexpected TestPyPI artifact count")
    name = f"codadapt-testpypi-distributions-{run_id}-{doc['run_attempt']}"
    matched = [artifact for artifact in artifacts["artifacts"] if artifact.get("name") == name and not artifact.get("expired", True)]
    require(len(matched) == 1, "Missing, ambiguous or expired verified TestPyPI artifact")
    artifact = matched[0]
    require(type(artifact.get("id")) is int and artifact["id"] > 0 and
            0 < artifact.get("size_in_bytes", 0) <= LIMIT and
            artifact.get("workflow_run", {}).get("id") == int(run_id), "Unexpected artifact provenance or size")
    output("artifact_id", str(artifact["id"]))
    print("PASS_MATCHING_TESTPYPI_RUN")


def distribution_files(directory):
    require(directory.is_dir() and {p.name for p in directory.iterdir()} == set(FILES), "Unexpected distribution set")
    result = {}
    for name in FILES:
        path = directory / name
        require(path.is_file() and not path.is_symlink(), "Unsafe distribution member: " + name)
        require(0 < path.stat().st_size <= LIMIT, "Unexpected distribution size")
        data = path.read_bytes()
        result[name] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    return result


def authenticate(directory):
    files = distribution_files(directory)
    for name, variable in zip(FILES, ("EXPECTED_WHEEL", "EXPECTED_SDIST")):
        digest = os.environ.get(variable, "")
        require(bool(re.fullmatch(r"[0-9a-f]{64}", digest)) and files[name]["sha256"] == digest,
                "Distribution digest mismatch: " + name)
    print("PASS_AUTHENTICATED_DISTRIBUTIONS")


def record_hashes(directory):
    files = distribution_files(directory)
    for name, key in zip(FILES, ("wheel_sha256", "sdist_sha256")):
        output(key, files[name]["sha256"])
        print(files[name]["sha256"] + "  " + name)


def output(name, value):
    require(bool(re.fullmatch(r"[a-z_][a-z0-9_]*", name)) and "\n" not in value and "\r" not in value, "Unsafe workflow output")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def classify_index(doc, files):
    if doc is None:
        return "EMPTY"
    info = doc.get("info", {})
    require(info.get("name", "").lower() == "codadapt" and info.get("version") == VERSION, "Wrong registry release")
    rows = doc.get("urls", [])
    by_name = {row["filename"]: row for row in rows}
    require(len(rows) == len(by_name) and set(by_name) == set(files), "Partial or unexpected release: stop for owner review")
    for name, expected in files.items():
        row = by_name[name]
        require(row.get("digests", {}).get("sha256") == expected["sha256"] and
                row.get("size") == expected["size"] and not row.get("yanked", False),
                "Existing registry file differs or is yanked: " + name)
    return "COMPLETE_IDENTICAL"


def index(channel, directory, phase):
    files = distribution_files(directory)
    base = INDEXES[channel]
    hosts = {urlsplit(base).hostname}
    project = json.loads(get(base + "/pypi/codadapt/json", hosts))
    require(project.get("info", {}).get("name", "").lower() == "codadapt", "Existing project required")
    # Allow time for registry indexing after a successful upload, but never upload
    # to an existing partial or different release.
    for attempt in range(7 if phase == "post" else 1):
        raw = get(base + f"/pypi/codadapt/{VERSION}/json", hosts, absent=True)
        doc = json.loads(raw) if raw is not None else None
        try:
            state = classify_index(doc, files)
            if phase == "pre" or state == "COMPLETE_IDENTICAL":
                break
        except RuntimeError:
            if phase == "pre" or attempt == 6:
                raise
        if attempt < 6:
            time.sleep(5)
    if phase == "pre" and state == "EMPTY":
        output("needs_upload", "true")
        print("EMPTY_REGISTRY_RELEASE")
        return
    require(state == "COMPLETE_IDENTICAL", "Required complete registry release not available")
    # Check actual downloaded bytes, not just registry metadata.
    for row in doc["urls"]:
        name = row["filename"]
        data = get(row["url"], CDNS[channel], limit=files[name]["size"])
        require(data == (directory / name).read_bytes(), "Downloaded bytes differ: " + name)
    if phase == "pre":
        output("needs_upload", "false")
    print("PASS_COMPLETE_IDENTICAL_" + channel.upper())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["gate", "test-run", "hashes", "authenticate", "index"])
    parser.add_argument("--channel", choices=list(INDEXES))
    parser.add_argument("--directory", type=Path, default=Path("dist"))
    parser.add_argument("--phase", choices=["pre", "post"])
    parser.add_argument("--run-id")
    args = parser.parse_args()
    if args.command == "gate":
        gate(args.channel)
    elif args.command == "test-run":
        verify_test_run(args.run_id)
    elif args.command == "hashes":
        record_hashes(args.directory)
    elif args.command == "authenticate":
        authenticate(args.directory)
    else:
        require(args.channel and args.phase, "Registry and phase required")
        index(args.channel, args.directory, args.phase)


if __name__ == "__main__":
    main()
