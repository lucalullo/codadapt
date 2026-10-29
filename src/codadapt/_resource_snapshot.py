"""Private, read-only resource observations; never grants model admission.

Visible limits and physical availability are observations, not reservations or
proof that a fit cannot OOM. Policy selection belongs to a separate protocol.
"""

import ctypes
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 65536
MAX_ANCESTORS = 64
MAX_CONTROLLER_PATHS = 8


def bounded_read(path):
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("Resource metadata exceeds bounded read size")
    return data.decode("utf-8")


def amount(value):
    value = value.strip()
    if not value.isascii() or not value.isdigit() or len(value) > 20:
        raise ValueError("Invalid nonnegative memory amount")
    result = int(value)
    if result > 2**64 - 1:
        raise ValueError("Memory amount overflow")
    return result


def snapshot(platform):
    return dict(
        platform=platform,
        total_bytes=None,
        available_bytes=None,
        process_RSS_bytes=None,
        commit_available_bytes=None,
        limits=[],
        uncertainties=[],
        scope_notes=[],
        status="UNKNOWN",
    )


def finish(result):
    total, available = result["total_bytes"], result["available_bytes"]
    if total is not None and available is not None:
        if total <= 0 or available < 0 or available > total:
            result["uncertainties"].append("Invalid OS memory observation")
            result["effective_capacity_bytes"] = None
            result["effective_available_bytes"] = None
        else:
            capacities = [total]
            headrooms = [available]
            if result["commit_available_bytes"] is not None:
                headrooms.append(result["commit_available_bytes"])
            for row in result["limits"]:
                capacities.append(row["limit_bytes"])
                if row["usage_bytes"] is not None:
                    headrooms.append(max(0, row["limit_bytes"] - row["usage_bytes"]))
                else:
                    result["uncertainties"].append("Known limit has unknown usage")
            result["effective_capacity_bytes"] = min(capacities)
            result["effective_available_bytes"] = min(headrooms)
            result["status"] = (
                "INCOMPLETE" if result["uncertainties"] else "OBSERVED_VISIBLE_LIMITS"
            )
    else:
        result["effective_capacity_bytes"] = None
        result["effective_available_bytes"] = None
    result["admission_granted"] = False
    result["policy_qualified"] = False
    return result


def kib_fields(text):
    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("Metadata too large")
    fields = {}
    for line in text.splitlines():
        match = re.fullmatch(r"([A-Za-z_()]+):\s+([0-9]+)\s+kB\s*", line)
        if match:
            fields[match[1]] = amount(match[2]) * 1024
    return fields


def clean_posix(value):
    value = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), value)
    path = PurePosixPath(value)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Unresolved cgroup namespace path")
    return path


def cgroup_observations(read, result):
    groups = []
    for line in read("/proc/self/cgroup").splitlines():
        fields = line.split(":", 2)
        if len(fields) != 3:
            raise ValueError("Malformed cgroup membership")
        if fields[1] == "" or "memory" in fields[1].split(","):
            groups.append(("v2" if fields[1] == "" else "v1", clean_posix(fields[2])))
    if len(groups) > MAX_CONTROLLER_PATHS:
        raise ValueError("Too many cgroup controller paths")
    mounts = []
    for line in read("/proc/self/mountinfo").splitlines():
        fields = line.split()
        if "-" not in fields:
            continue
        sep = fields.index("-")
        if sep < 5 or len(fields) < sep + 4:
            raise ValueError("Malformed mountinfo")
        kind = fields[sep + 1]
        if kind == "cgroup2" or (kind == "cgroup" and "memory" in fields[sep + 3].split(",")):
            mounts.append(
                (
                    "v2" if kind == "cgroup2" else "v1",
                    clean_posix(fields[3]),
                    clean_posix(fields[4]),
                )
            )
    if len(mounts) > MAX_CONTROLLER_PATHS:
        raise ValueError("Too many cgroup memory mounts")
    for version, member in groups:
        choices = [m for m in mounts if m[0] == version and member.is_relative_to(m[1])]
        if not choices:
            raise ValueError("Cgroup membership/mount mapping unresolved")
        # The most specific visible bind mount bounds the accessible hierarchy.
        _, mount_root, mount_point = max(choices, key=lambda row: len(row[1].parts))
        current = mount_point / member.relative_to(mount_root)
        seen = 0
        while True:
            seen += 1
            if seen > MAX_ANCESTORS:
                raise ValueError("Cgroup ancestor bound reached")
            prefix = "memory.max" if version == "v2" else "memory.limit_in_bytes"
            usage_name = "memory.current" if version == "v2" else "memory.usage_in_bytes"
            try:
                raw = read(str(current / prefix)).strip()
            except FileNotFoundError:
                if current == mount_point and mount_root == PurePosixPath("/"):
                    result["scope_notes"].append("Visible hierarchy root has no memory limit file")
                    break
                raise
            limit = None if version == "v2" and raw == "max" else amount(raw)
            if version == "v1" and limit is not None and limit >= 2**60:
                limit = None
            if limit is not None:
                usage = amount(read(str(current / usage_name)))
                result["limits"].append(
                    dict(
                        source=version,
                        path=str(current),
                        limit_bytes=limit,
                        usage_bytes=usage,
                        usage_semantics="current hierarchical cgroup charge",
                    )
                )
            if current == mount_point:
                break
            current = current.parent
        result["scope_notes"].append(
            "Only visible cgroup ancestors observed; hidden namespace ancestors are not certified"
        )


def linux(read=bounded_read):
    result = snapshot("Linux")
    calls = 0

    def bounded(path):
        nonlocal calls
        calls += 1
        if calls > 2 * MAX_ANCESTORS * MAX_CONTROLLER_PATHS + 4:
            raise ValueError("Resource read count bound reached")
        text = read(path)
        if len(text.encode("utf-8")) > MAX_FILE_BYTES:
            raise ValueError("Metadata too large")
        return text

    try:
        info = kib_fields(bounded("/proc/meminfo"))
        result["total_bytes"] = info["MemTotal"]
        result["available_bytes"] = info["MemAvailable"]
    except (OSError, ValueError, KeyError) as error:
        result["uncertainties"].append("OS memory unavailable: " + type(error).__name__)
    try:
        result["process_RSS_bytes"] = kib_fields(bounded("/proc/self/status"))["VmRSS"]
    except (OSError, ValueError, KeyError) as error:
        result["uncertainties"].append("Process RSS unavailable: " + type(error).__name__)
    try:
        cgroup_observations(bounded, result)
    except (OSError, ValueError) as error:
        result["uncertainties"].append("Container limits unresolved: " + str(error))
    result["read_calls"] = calls
    result["scope_notes"].append(
        "Available/usage already includes resident process/input; no second subtraction"
    )
    return finish(result)


def windows():
    from ctypes import wintypes as w

    result = snapshot("Windows")

    class Memory(ctypes.Structure):
        _fields_ = [("length", w.DWORD), ("load", w.DWORD)] + [
            (name, ctypes.c_ulonglong)
            for name in [
                "total",
                "available",
                "commit_total",
                "commit_available",
                "virtual_total",
                "virtual_available",
                "extended",
            ]
        ]

    class ProcessMemory(ctypes.Structure):
        _fields_ = [("size", w.DWORD), ("faults", w.DWORD)] + [
            (name, ctypes.c_size_t)
            for name in [
                "peak",
                "rss",
                "paged_peak",
                "paged",
                "nonpaged_peak",
                "nonpaged",
                "pagefile",
                "pagefile_peak",
            ]
        ]

    class BasicLimits(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_longlong),
            ("job_time", ctypes.c_longlong),
            ("flags", w.DWORD),
            ("working_min", ctypes.c_size_t),
            ("working_max", ctypes.c_size_t),
            ("active", w.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority", w.DWORD),
            ("scheduling", w.DWORD),
        ]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("basic", BasicLimits),
            ("io", ctypes.c_ulonglong * 6),
            ("process_limit", ctypes.c_size_t),
            ("job_limit", ctypes.c_size_t),
            ("process_peak", ctypes.c_size_t),
            ("job_peak", ctypes.c_size_t),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = w.HANDLE
    process = kernel.GetCurrentProcess()
    kernel.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(Memory)]
    kernel.GlobalMemoryStatusEx.restype = w.BOOL
    info = Memory()
    info.length = ctypes.sizeof(info)
    if kernel.GlobalMemoryStatusEx(ctypes.byref(info)):
        result.update(
            total_bytes=info.total,
            available_bytes=info.available,
            commit_available_bytes=info.commit_available,
            virtual_available_bytes=info.virtual_available,
            virtual_capacity_bytes=info.virtual_total,
        )
    else:
        result["uncertainties"].append("GlobalMemoryStatusEx failed")
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.POINTER(ProcessMemory), w.DWORD]
    psapi.GetProcessMemoryInfo.restype = w.BOOL
    counters = ProcessMemory()
    counters.size = ctypes.sizeof(counters)
    if psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.size):
        result["process_RSS_bytes"] = counters.rss
    else:
        result["uncertainties"].append("GetProcessMemoryInfo failed")
    kernel.IsProcessInJob.argtypes = [w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)]
    kernel.IsProcessInJob.restype = w.BOOL
    in_job = w.BOOL()
    if not kernel.IsProcessInJob(process, None, ctypes.byref(in_job)):
        result["uncertainties"].append("Windows job membership unknown")
    elif in_job.value:
        kernel.QueryInformationJobObject.argtypes = [
            w.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            w.DWORD,
            ctypes.c_void_p,
        ]
        kernel.QueryInformationJobObject.restype = w.BOOL
        job = ExtendedLimits()
        if kernel.QueryInformationJobObject(None, 9, ctypes.byref(job), ctypes.sizeof(job), None):
            for flag, name, limit, used in [
                (0x100, "process", job.process_limit, job.process_peak),
                (0x200, "job", job.job_limit, job.job_peak),
            ]:
                if job.basic.flags & flag:
                    result["limits"].append(
                        dict(
                            source="Windows_" + name,
                            limit_bytes=limit,
                            usage_bytes=used,
                            usage_semantics="lifetime peak charge, conservative relative to current",
                        )
                    )
            result["job_limit_flags"] = job.basic.flags
            result["scope_notes"].append(
                "Current job queried; inaccessible nested ancestor limits are not certified"
            )
        else:
            result["uncertainties"].append("Windows job limits unreadable")
    result["in_windows_job"] = bool(in_job.value)
    result["scope_notes"].append(
        "Physical and commit headroom observed; no RAM reservation or OOM guarantee"
    )
    return finish(result)


def macos_parse(total, vm, rss):
    result = snapshot("Darwin")
    result["total_bytes"] = amount(total)
    page = re.search(r"page size of ([0-9]+) bytes", vm)
    if not page:
        raise ValueError("vm_stat page size missing")
    fields = {}
    for line in vm.splitlines():
        match = re.fullmatch(r"(Pages free|Pages inactive):\s*([0-9]+)\.\s*", line)
        if match:
            fields[match[1]] = amount(match[2])
    result["available_bytes"] = (fields["Pages free"] + fields["Pages inactive"]) * amount(page[1])
    result["process_RSS_bytes"] = amount(rss) * 1024
    result["scope_notes"].append(
        "Conservative free+inactive page proxy; no extra speculative/purgeable double counting; actual macOS hardware unqualified"
    )
    return finish(result)


def macos(run=subprocess.run):
    result = snapshot("Darwin")
    try:
        values = []
        for command in [
            ["/usr/sbin/sysctl", "-n", "hw.memsize"],
            ["/usr/bin/vm_stat"],
            ["/bin/ps", "-o", "rss=", "-p", str(os.getpid())],
        ]:
            raw = run(command, capture_output=True, timeout=2, check=True).stdout
            if len(raw) > MAX_FILE_BYTES:
                raise ValueError("OS command output too large")
            values.append(raw.decode("ascii").strip())
        return macos_parse(*values)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        result["uncertainties"].append("macOS observation unavailable: " + type(error).__name__)
        return finish(result)


def observe():
    if sys.platform == "win32":
        return windows()
    if sys.platform.startswith("linux"):
        return linux()
    if sys.platform == "darwin":
        return macos()
    result = snapshot(sys.platform)
    result["uncertainties"].append("Unsupported platform")
    return finish(result)
