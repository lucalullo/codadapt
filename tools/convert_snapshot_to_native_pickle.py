"""Extract an authenticated native pickle from a trusted CodAdapt snapshot.

No pickle content is executed. Load the result only in a trusted compatible
native environment. Existing output files are never overwritten.
"""
from pathlib import Path
import argparse,hashlib,os,struct,zlib
MAGIC=b"CDA74TEC";HEADER="<BQ32s";LIMIT=32*1024**2
def extract_native(wire):
    n=8+struct.calcsize(HEADER)
    if len(wire)<n or wire[:8]!=MAGIC:raise ValueError("Unsupported snapshot header")
    compressed,size,digest=struct.unpack(HEADER,wire[8:n])
    if compressed not in (0,1) or size>LIMIT:raise ValueError("Invalid bounds")
    if compressed:
        d=zlib.decompressobj();raw=d.decompress(wire[n:],size+1)
        if not d.eof or d.unused_data or d.unconsumed_tail:raise ValueError("Invalid compressed extent")
    else:raw=wire[n:]
    if len(raw)!=size or hashlib.sha256(raw).digest()!=digest:raise ValueError("Snapshot digest/length mismatch")
    return raw
def convert(source,destination,expected_sha256):
    source=Path(source)
    if source.stat().st_size>33*1024**2:raise ValueError("File exceeds bound")
    wire=source.read_bytes()
    if hashlib.sha256(wire).hexdigest()!=expected_sha256:raise ValueError("File digest mismatch")
    raw=extract_native(wire)
    with Path(destination).open("xb") as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return {"bytes":len(raw),"SHA256":hashlib.sha256(raw).hexdigest()}
def main():
    p=argparse.ArgumentParser();p.add_argument("source");p.add_argument("destination")
    p.add_argument("--expected-sha256",required=True);a=p.parse_args();print(convert(a.source,a.destination,a.expected_sha256))
if __name__=="__main__":main()

