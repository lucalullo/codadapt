"""Normalize a standard 2.1.0 sdist reproducibly; never modify package contents."""
from pathlib import Path,PurePosixPath
import argparse,gzip,io,tarfile

def normalize(source,destination,epoch):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if source==destination or destination.exists() or epoch<0:raise ValueError('New destination and nonnegative epoch required')
    with tarfile.open(source) as archive:
        records={};total=0
        for member in archive:
            name=member.name.rstrip('/');parts=name.split('/')
            if (PurePosixPath(name).is_absolute() or '\\' in name or ':' in name
                    or any(p in ('','.','..','.git','PRIVATE_CODEX','__pycache__') for p in parts)
                    or not parts or parts[0]!='codadapt-2.1.0'):
                raise ValueError('Unsafe/non-distributable source member')
            if not (member.isdir() or member.isfile()) or name.casefold() in records:raise ValueError('Source link/alias forbidden')
            total+=member.size
            if total>150*1024**2:raise ValueError('Source archive expansion exceeds budget')
            records[name.casefold()]=(name,member,archive.extractfile(member).read() if member.isfile() else None)
    with destination.open('xb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=9) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT) as output:
                for name,member,data in sorted(records.values(),key=lambda row:row[0]):
                    info=tarfile.TarInfo(name);info.mtime=epoch;info.uid=info.gid=0;info.uname=info.gname=''
                    info.mode=0o755 if member.isdir() or member.mode&0o111 else 0o644
                    if member.isdir():info.type=tarfile.DIRTYPE;output.addfile(info)
                    else:info.size=len(data);output.addfile(info,io.BytesIO(data))
    return dict(files=sum(data is not None for _,_,data in records.values()),bytes_uncompressed=total,epoch=epoch,contents_changed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('destination',type=Path);p.add_argument('--epoch',type=int,required=True);a=p.parse_args()
    print(normalize(a.source,a.destination,a.epoch))
