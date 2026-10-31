"""Offline failure controls for the manual immutable-release publication guard.

No credentials, network requests, builds or uploads are used. Filesystem probes
stay under CODADAPT_TEST_EXTERNAL_TMP, outside the source repository and within
the private laboratory when this suite is executed locally.
"""
from copy import deepcopy
import csv
import io
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "codadapt_publication_guard_offline", ROOT / "tools/publication_guard.py"
)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

APPROVED = b"# CodAdapt\n\npip install codadapt\n"
COMMIT = "a" * 40


def contract():
    # Synthetic four-file unit contract. These hashes are NOT release evidence.
    p = {
        "project": "codadapt",
        "version": "2.1.0",
        "repository": "lucalullo/codadapt",
        "owner": "lucalullo",
        "branch": "main",
        "workflow_files": {
            "testpypi": "publish-testpypi.yml",
            "pypi": "publish-pypi.yml",
        },
        "environments": {"testpypi": "testpypi", "pypi": "pypi"},
        "bundle_SHA256": "b" * 64,
        "distribution_manifest_SHA256": "d" * 64,
        "required_distribution_count": 4,
        "publication_set_status": "READY_FOUR_VERIFIED",
        "README_SHA256": guard.digest(APPROVED),
        "source_manifest_SHA256": "c" * 64,
        "distributions": {
            "pure/codadapt-2.1.0-py3-none-any.whl": {"SHA256": "1" * 64, "bytes": 111},
            "native_windows/codadapt-2.1.0-cp312-cp312-win_amd64.whl": {
                "SHA256": "2" * 64, "bytes": 222, "native_kernel_SHA256": "4" * 64
            },
            "source/codadapt-2.1.0.tar.gz": {"SHA256": "3" * 64, "bytes": 333},
            "native_linux/codadapt-2.1.0-cp313-cp313-manylinux_2_28_x86_64.whl": {
                "SHA256": "5" * 64, "bytes": 444,
            },
        },
    }
    p['manylinux_evidence'] = {
        'status': 'VERIFIED_ORIGINAL_ARTIFACT', 'provenance_verified': True,
        'approved_commit': 'e' * 40, 'source_commit': 'e' * 40,
        'repository': p['repository'], 'conclusion': 'success',
        'run_id': 123, 'run_attempt': 1, 'artifact_id': 456,
        'wheel_filename': 'codadapt-2.1.0-cp313-cp313-manylinux_2_28_x86_64.whl',
        'wheel_SHA256': '5' * 64, 'README_SHA256': p['README_SHA256'],
        'qualification_receipt_SHA256': '6' * 64,
    }
    return p


def index_doc(p):
    return {
        "info": {"name": "codadapt", "version": "2.1.0"},
        "urls": [
            {"filename": name, "digests": {"sha256": r["SHA256"]},
             "size": r["bytes"], "yanked": False}
            for name, r in guard.expected_files(p).items()
        ],
    }


def environment_doc(channel="pypi"):
    return {
        "name": channel,
        "can_admins_bypass": False,
        "protection_rules": [{
            "type": "required_reviewers",
            "prevent_self_review": False,
            "reviewers": [{"type": "User", "reviewer": {"login": "lucalullo"}}],
        }],
    }


def run_doc():
    return {
        "id": 42, "status": "completed", "conclusion": "success",
        "event": "workflow_dispatch", "path": ".github/workflows/publish-testpypi.yml",
        "head_sha": COMMIT, "head_branch": "main", "run_attempt": 2,
        "repository": {"full_name": "lucalullo/codadapt"},
        "head_repository": {"full_name": "lucalullo/codadapt"},
        "actor": {"login": "lucalullo"}, "triggering_actor": {"login": "lucalullo"},
    }


def receipt_doc(p):
    return {
        "status": "PASS_TESTPYPI_DOWNLOAD_AND_CONSUMERS",
        "repository": p["repository"], "workflow": "publish-testpypi.yml",
        "head_sha": COMMIT, "run_id": "42", "run_attempt": "2",
        "bundle_SHA256": p["bundle_SHA256"], "README_SHA256": p["README_SHA256"],
        "files": guard.expected_files(p), "native_calls": 200, "exact_arrays": 35,
        "source_manifest_SHA256": p["source_manifest_SHA256"],
        **guard.release_binding(p),
    }


class OfflineGuardTests(unittest.TestCase):
    def setUp(self):
        # Any accidental network operation fails the test before a socket is opened.
        self.network = patch.object(guard.urllib.request, "build_opener", side_effect=AssertionError("Network forbidden in unit tests"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.p = contract()

    def actual_manylinux(self):
        name = os.environ.get('CODADAPT_TEST_MANYLINUX_WHEEL')
        if not name:
            self.skipTest('Actual approved manylinux wheel required')
        wheel = Path(name)
        p = json.loads((ROOT/'qualification/PUBLICATION_210.json').read_bytes())
        return wheel, p, (ROOT/'README.md').read_bytes()

    def test_actual_manylinux_wheel_accepts_explicit_zip_directories(self):
        wheel, p, approved = self.actual_manylinux()
        with zipfile.ZipFile(wheel) as archive:
            self.assertTrue(any(m.is_dir() for m in archive.infolist()))
        guard.check_distribution(wheel.name, wheel.read_bytes(), approved, p)

    def test_regular_file_missing_from_record_is_rejected(self):
        wheel, p, approved = self.actual_manylinux()
        buffer = io.BytesIO()
        with zipfile.ZipFile(wheel) as original, zipfile.ZipFile(buffer, 'w') as changed:
            record, = [n for n in original.namelist() if n.endswith('.dist-info/RECORD')]
            rows = list(csv.reader(io.StringIO(original.read(record).decode())))
            missing = next(r[0] for r in rows if r[0].endswith('.py'))
            out = io.StringIO(newline='')
            csv.writer(out).writerows([r for r in rows if r[0] != missing])
            for member in original.infolist():
                changed.writestr(member, out.getvalue().encode() if member.filename == record else original.read(member))
        raw = buffer.getvalue()
        fixture = deepcopy(p)
        row = next(r for n,r in fixture['distributions'].items() if Path(n).name == wheel.name)
        row.update(SHA256=guard.digest(raw), bytes=len(raw))
        with self.assertRaisesRegex(ValueError, 'Incomplete RECORD'):
            guard.check_distribution(wheel.name, raw, approved, fixture)

    def test_four_distributions_required_missing_or_extra_rejected(self):
        guard.validate_release_set(self.p)
        self.assertEqual(len(guard.expected_files(self.p)), 4)
        for count in (0, 3, 5):
            p = deepcopy(self.p)
            if count < 4:
                p['distributions'] = dict(list(p['distributions'].items())[:count])
            else:
                p['distributions']['extra/codadapt-other.whl'] = {'SHA256': 'a'*64, 'bytes': 123}
            with self.subTest(count=count), self.assertRaises(ValueError):
                guard.expected_files(p)

    def test_raw_linux_wheel_cannot_replace_manylinux(self):
        p = deepcopy(self.p)
        name = next(n for n in p['distributions'] if 'manylinux' in n)
        p['distributions'][name.replace('manylinux_2_28_x86_64', 'linux_x86_64')] = p['distributions'].pop(name)
        with self.assertRaises(ValueError):
            guard.validate_release_set(p)

    def test_manylinux_provenance_readme_commit_and_hash_are_required(self):
        for field, value in [('approved_commit', None), ('source_commit', 'f'*40),
                             ('wheel_SHA256', 'f'*64), ('README_SHA256', 'a'*64),
                             ('provenance_verified', False), ('conclusion', 'failure'),
                             ('repository', 'other/codadapt'), ('artifact_id', None),
                             ('run_id', True), ('qualification_receipt_SHA256', None)]:
            p = deepcopy(self.p)
            p['manylinux_evidence'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                guard.validate_release_set(p)

    def test_pending_policy_cannot_reuse_the_old_bundle_or_create_upload_files(self):
        p = deepcopy(self.p)
        p['publication_set_status'] = 'HOLD_MISSING_MANYLINUX'
        p['bundle_SHA256'] = None
        with patch.object(guard, 'check_source') as source, patch.object(guard, 'stage') as stage:
            with self.assertRaises(ValueError):
                guard.prepare(Path('unused'), p)
            source.assert_not_called()
            stage.assert_not_called()

    def test_old_three_file_receipt_cannot_promote_four_file_release(self):
        good = receipt_doc(self.p)
        with patch.dict(os.environ, {'GITHUB_SHA': COMMIT}, clear=True):
            for field in ('distribution_count', 'manylinux_wheel_SHA256', 'manylinux_approved_commit',
                          'manylinux_qualification_receipt_SHA256'):
                changed = deepcopy(good)
                changed.pop(field)
                with self.subTest(field=field), self.assertRaises(ValueError):
                    guard.validate_receipt(changed, '42', '2', self.p)

    def test_index_absent_and_complete_identical(self):
        self.assertEqual(guard.classify_index(None, self.p), "EMPTY")
        self.assertEqual(guard.classify_index(index_doc(self.p), self.p), "COMPLETE_IDENTICAL")

    def test_index_partial_empty_and_unexpected_are_not_uploadable(self):
        complete = index_doc(self.p)
        extra = deepcopy(complete["urls"][0])
        extra["filename"] = "codadapt-2.1.0-other.whl"
        for urls in ([], complete["urls"][:-1], complete["urls"] + [extra]):
            with self.subTest(files=[x["filename"] for x in urls]), self.assertRaises(ValueError):
                guard.classify_index({"info": complete["info"], "urls": urls}, self.p)

    def test_index_duplicate_mismatch_yanked_and_wrong_identity_rejected(self):
        for label in ("duplicate", "hash", "size", "yanked", "name", "version"):
            doc = index_doc(self.p)
            if label == "duplicate":
                doc["urls"].append(deepcopy(doc["urls"][0]))
            elif label == "hash":
                doc["urls"][0]["digests"]["sha256"] = "0" * 64
            elif label == "size":
                doc["urls"][0]["size"] += 1
            elif label == "yanked":
                doc["urls"][0]["yanked"] = True
            elif label == "name":
                doc["info"]["name"] = "other"
            else:
                doc["info"]["version"] = "2.1.1"
            with self.subTest(label=label), self.assertRaises(ValueError):
                guard.classify_index(doc, self.p)

    def test_environment_requires_the_existing_exact_name(self):
        guard.validate_environment(environment_doc(), "pypi", self.p)
        guard.validate_environment({"name": "testpypi"}, "testpypi", self.p)
        for channel in ("pypi", "testpypi"):
            with self.subTest(channel=channel), self.assertRaises(ValueError):
                guard.validate_environment({"name": "new-environment"}, channel, self.p)

    def test_pypi_missing_review_bypass_wrong_reviewer_and_self_review_rejected(self):
        for label in ("missing", "multiple", "bypass", "missing_bypass", "foreign", "team", "missing_reviewer", "self_review", "missing_self_review"):
            doc = environment_doc()
            rule = doc["protection_rules"][0]
            if label == "missing":
                doc["protection_rules"] = []
            elif label == "multiple":
                doc["protection_rules"].append(deepcopy(rule))
            elif label == "bypass":
                doc["can_admins_bypass"] = True
            elif label == "missing_bypass":
                del doc["can_admins_bypass"]
            elif label == "foreign":
                rule["reviewers"][0]["reviewer"]["login"] = "someone-else"
            elif label == "team":
                rule["reviewers"][0]["type"] = "Team"
            elif label == "missing_reviewer":
                rule["reviewers"] = []
            elif label == "self_review":
                rule["prevent_self_review"] = True
            else:
                del rule["prevent_self_review"]
            with self.subTest(label=label), self.assertRaises(ValueError):
                guard.validate_environment(doc, "pypi", self.p)

    def test_metadata_preserves_exact_readme_and_rejects_changed_content(self):
        header = b"Metadata-Version: 2.4\nName: codadapt\nVersion: 2.1.0\nDescription-Content-Type: text/markdown\n\n"
        guard.metadata(header + APPROVED, APPROVED)
        for body in (APPROVED.replace(b"\n", b"\r\n"), APPROVED + b"\n", APPROVED.replace(b"pip install", b"python -m pip install")):
            with self.subTest(body=body), self.assertRaises(ValueError):
                guard.metadata(header + body, APPROVED)

    def test_metadata_rejects_wrong_name_version_and_description_type(self):
        header = b"Metadata-Version: 2.4\nName: codadapt\nVersion: 2.1.0\nDescription-Content-Type: text/markdown\n\n"
        for before, after in ((b"Name: codadapt", b"Name: other"), (b"Version: 2.1.0", b"Version: 2.1.1"), (b"text/markdown", b"text/plain")):
            with self.subTest(after=after), self.assertRaises(ValueError):
                guard.metadata(header.replace(before, after) + APPROVED, APPROVED)

    def test_archive_safe_paths(self):
        for name in ("README.md", "src/codadapt/core.py", "codadapt-2.1.0/", "a/.hidden"):
            guard.safe_member(name)
        for name in ("", "/absolute", "../escape", "a/../escape", "./file", "a//file", "C:/escape", "a\\file", "a/./file", "//server/file"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                guard.safe_member(name)

    def test_hash_and_size_both_bound(self):
        raw = b"qualified bytes"
        good = {"SHA256": guard.digest(raw), "bytes": len(raw)}
        guard.check_hash(raw, good, "unit")
        for bad in ({**good, "SHA256": "0" * 64}, {**good, "bytes": 0}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                guard.check_hash(raw, bad, "unit")

    def test_stage_refuses_outputs_inside_source_before_creating_them(self):
        target = ROOT / "publication_guard_forbidden_output"
        self.assertFalse(target.exists())
        with self.assertRaises(ValueError):
            guard.stage(target)
        self.assertFalse(target.exists())

    def test_validate_run_successful_manual_same_commit_repository_and_owner(self):
        with patch.dict(os.environ, {"GITHUB_SHA": COMMIT}, clear=True):
            guard.validate_run(run_doc(), "42", self.p)
            changes = {
                "id": 43, "status": "in_progress", "conclusion": "failure", "event": "push",
                "path": ".github/workflows/other.yml", "head_sha": "d" * 40, "head_branch": "other",
                "repository": {"full_name": "fork/codadapt"},
                "head_repository": {"full_name": "fork/codadapt"},
                "actor": {"login": "other"}, "triggering_actor": {"login": "other"},
            }
            for key, value in changes.items():
                doc = run_doc()
                doc[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    guard.validate_run(doc, "42", self.p)

    def test_validate_run_requires_real_positive_integer_attempt(self):
        with patch.dict(os.environ, {"GITHUB_SHA": COMMIT}, clear=True):
            for attempt in (None, 0, -1, "2", 1.5, True):
                doc = run_doc()
                doc["run_attempt"] = attempt
                with self.subTest(attempt=attempt), self.assertRaises(ValueError):
                    guard.validate_run(doc, "42", self.p)

    def test_receipt_binds_commit_hashes_attempt_files_and_execution_evidence(self):
        with patch.dict(os.environ, {"GITHUB_SHA": COMMIT}, clear=True):
            good = receipt_doc(self.p)
            guard.validate_receipt(good, "42", "2", self.p)
            for key in good:
                changed = deepcopy(good)
                changed[key] = {} if key == "files" else "invalid"
                with self.subTest(key=key), self.assertRaises(ValueError):
                    guard.validate_receipt(changed, "42", "2", self.p)
            with self.assertRaises(ValueError):
                guard.validate_receipt(good, "42", "3", self.p)

    def test_gate_is_manual_owner_only_and_checks_existing_environment(self):
        for channel in ("testpypi", "pypi"):
            env = self.gate_env(channel)
            with patch.dict(os.environ, env, clear=True), patch.object(guard, "check_source", return_value=APPROVED) as source, patch.object(guard, "gh", return_value=environment_doc(channel)) as gh:
                guard.gate(channel, self.p)
                source.assert_called_once_with(self.p)
                gh.assert_called_once_with("/repos/lucalullo/codadapt/environments/" + channel)

    def gate_env(self, channel):
        return {
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REPOSITORY": "lucalullo/codadapt",
            "GITHUB_REF": "refs/heads/main", "GITHUB_ACTOR": "lucalullo", "GITHUB_TRIGGERING_ACTOR": "lucalullo",
            "GITHUB_WORKFLOW_REF": "lucalullo/codadapt/.github/workflows/" + self.p["workflow_files"][channel] + "@refs/heads/main",
            "TRUSTED_PUBLISHER_CONFIRMED": "true",
            "OWNER_APPROVAL": ("TEST" if channel == "testpypi" else "PUBLISH") + " codadapt 2.1.0",
        }

    def test_gate_rejects_unsafe_context_before_api_request(self):
        changes = {
            "GITHUB_EVENT_NAME": "push", "GITHUB_REPOSITORY": "fork/codadapt",
            "GITHUB_REF": "refs/heads/feature", "GITHUB_ACTOR": "other", "GITHUB_TRIGGERING_ACTOR": "other",
            "GITHUB_WORKFLOW_REF": "lucalullo/codadapt/.github/workflows/renamed.yml@refs/heads/main",
            "TRUSTED_PUBLISHER_CONFIRMED": "false", "OWNER_APPROVAL": "yes",
        }
        for key, value in changes.items():
            env = self.gate_env("pypi")
            env[key] = value
            with self.subTest(key=key), patch.dict(os.environ, env, clear=True), patch.object(guard, "check_source", return_value=APPROVED), patch.object(guard, "gh") as gh, self.assertRaises(ValueError):
                guard.gate("pypi", self.p)
            gh.assert_not_called()

    def test_gate_source_failure_stops_before_api(self):
        with patch.dict(os.environ, self.gate_env("pypi"), clear=True), patch.object(guard, "check_source", side_effect=ValueError("changed source")), patch.object(guard, "gh") as gh, self.assertRaises(ValueError):
            guard.gate("pypi", self.p)
        gh.assert_not_called()

    def test_fetch_malformed_urls_rejected_without_network_or_writes(self):
        base = os.environ.get("CODADAPT_TEST_EXTERNAL_TMP")
        tmp_root = Path(base) if base else ROOT.parent / "work" / "publication_guard_tests"
        tmp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root, prefix="url_reject_") as temp:
            directory = Path(temp)
            urls = [
                "http://github.com/lucalullo/codadapt/releases/download/x/bundle.zip",
                "https://evil.example/lucalullo/codadapt/releases/download/x/bundle.zip",
                "https://user:password@github.com/lucalullo/codadapt/releases/download/x/bundle.zip",
                "https://github.com:444/lucalullo/codadapt/releases/download/x/bundle.zip",
                "https://github.com/other/project/releases/download/x/bundle.zip",
                "https://github.com/lucalullo/codadapt/releases/download/x/bundle.zip?token=dummy",
                "https://github.com/lucalullo/codadapt/releases/download/x/bundle.zip#fragment",
                "https://github.com/user-attachments/files/not-numeric/bundle.zip",
                "https://github.com/user-attachments/files/123/not-a-zip.txt",
            ]
            for url in urls:
                with self.subTest(url=url), patch.dict(os.environ, {"BUNDLE_URL": url}, clear=True), self.assertRaises(ValueError):
                    guard.fetch(directory, self.p)
            self.assertEqual(list(directory.iterdir()), [])

    def test_get_credentials_never_sent_to_non_api_host(self):
        with self.assertRaises(ValueError):
            guard.get("https://github.com/public", {"github.com"}, token="unit-test-token")

    def test_redirect_rejects_foreign_host_http_credentials_and_auth_forwarding(self):
        handler = guard.CheckedRedirect({"github.com"})
        request = urllib.request.Request("https://github.com/start")
        for url in ("https://evil.example/file", "http://github.com/file", "https://user:password@github.com/file", "https://github.com:444/file"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                handler.redirect_request(request, None, 302, "Found", {}, url)
        authorized = urllib.request.Request("https://github.com/start", headers={"Authorization": "Bearer unit-test-token"})
        with self.assertRaises(ValueError):
            handler.redirect_request(authorized, None, 302, "Found", {}, "https://github.com/file")


if __name__ == "__main__":
    unittest.main()
