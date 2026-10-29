"""Bound and reap observed owned subprocesses; never operate on unrelated PIDs."""
import subprocess
import time
import psutil


def run_owned(command, *, cwd, env, stdout, stderr, timeout=300, max_rss=1536*1024**2):
    if timeout <= 0 or max_rss <= 0:
        raise ValueError('Positive command time and memory budgets required')
    start=time.monotonic()
    process=subprocess.Popen(command,cwd=cwd,env=env,stdout=stdout,stderr=stderr)
    root=psutil.Process(process.pid)
    owned={process.pid:root.create_time()}
    peak=0;reason=None;cleanup=[]

    def current():
        result=[]
        for pid,birth in tuple(owned.items()):
            try:
                candidate=psutil.Process(pid)
                if abs(candidate.create_time()-birth)<.01 and candidate.is_running():result.append(candidate)
            except psutil.NoSuchProcess:pass
        return result

    def collect():
        for parent in current():
            try:
                for child in parent.children(recursive=True):owned.setdefault(child.pid,child.create_time())
            except psutil.NoSuchProcess:pass

    def stop():
        collect()
        remaining=current()
        # Kill descendants before root; verify birth identities again per process.
        for candidate in sorted(remaining,key=lambda p:p.pid==process.pid):
            try:
                if abs(candidate.create_time()-owned[candidate.pid])<.01:
                    candidate.kill();cleanup.append(candidate.pid)
            except psutil.NoSuchProcess:pass
        psutil.wait_procs(remaining,timeout=5)

    try:
        while True:
            collect()
            alive=current()
            rss=0
            for candidate in alive:
                try:rss+=candidate.memory_info().rss
                except psutil.NoSuchProcess:pass
            peak=max(peak,rss)
            if rss>max_rss:reason='OWNED_TREE_RSS_LIMIT';stop();break
            if time.monotonic()-start>timeout:reason='COMMAND_TIMEOUT';stop();break
            if process.poll() is not None:
                if any(p.pid!=process.pid for p in alive):stop()
                break
            time.sleep(.025)
    except BaseException:
        stop()
        raise
    process.wait(timeout=5)
    live=[p.pid for p in current() if p.status()!=psutil.STATUS_ZOMBIE]
    if live:raise RuntimeError('Recorded owned child processes remain: '+repr(live))
    return dict(returncode=124 if reason=='COMMAND_TIMEOUT' else 137 if reason else process.returncode,
        process_returncode=process.returncode,seconds=time.monotonic()-start,
        sampled_owned_tree_peak_RSS=peak,resource_stop=reason,
        owned_process_births={str(k):v for k,v in owned.items()},owned_cleanup_pids=cleanup,
        active_recorded_owned_processes=0,
        ownership_scope='Observed PID and birth-verified descendants; no unrelated process scan')
