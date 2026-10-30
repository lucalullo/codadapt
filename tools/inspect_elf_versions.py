"""Read ELF64 version requirements without loading a returned native library."""
from pathlib import Path
import argparse,hashlib,json,struct,zipfile

def inspect(data):
    if len(data)<64 or data[:6]!=b'\x7fELF\x02\x01':raise ValueError('Expected little-endian ELF64')
    def unpack(fmt,offset):
        if offset<0 or offset+struct.calcsize(fmt)>len(data):raise ValueError('Truncated ELF')
        return struct.unpack_from(fmt,data,offset)
    machine=unpack('<H',18)[0]
    shoff=unpack('<Q',40)[0];entry_size,count=unpack('<HH',58)
    if entry_size<64 or count>65535:raise ValueError('Invalid ELF section table')
    sections=[unpack('<IIQQQQIIQQ',shoff+i*entry_size) for i in range(count)]
    needed=[]
    for s in sections:
        if s[1]!=0x6ffffffe:continue
        if s[6]>=len(sections):raise ValueError('Invalid version string table')
        strings=sections[s[6]];start,end=s[4],s[4]+s[5]
        if end>len(data):raise ValueError('Truncated version section')
        def string(index):
            a=strings[4]+index;b=data.find(b'\0',a,strings[4]+strings[5])
            if a<strings[4] or b<0 or b>len(data):raise ValueError('Invalid ELF version string')
            return data[a:b].decode('ascii')
        cursor=start;seen=set()
        while cursor<end:
            if cursor in seen:raise ValueError('Cyclic ELF versions')
            seen.add(cursor)
            version,n,file_index,aux,next_entry=unpack('<HHIII',cursor)
            if version!=1:raise ValueError('Unsupported verneed version')
            values=[];a=cursor+aux
            for _ in range(n):
                if not start<=a<end:raise ValueError('Invalid version auxiliary offset')
                _,_,_,name,next_aux=unpack('<IHHII',a);values.append(string(name));a+=next_aux
            needed.append(dict(library=string(file_index),versions=values))
            if not next_entry:break
            cursor+=next_entry
    return dict(ELF='ELF64 little-endian',machine=machine,requirements=needed,
                scope='Static required symbol versions only; not a runtime/manylinux certification')

def wheel_info(path):
    with zipfile.ZipFile(path) as z:
        if z.testzip() is not None:raise ValueError('Corrupt wheel')
        names=[n for n in z.namelist() if n.startswith('codadapt/_native_kernel') and n.endswith('.so')]
        if len(names)!=1:raise ValueError('Expected one actual Linux kernel')
        data=z.read(names[0])
        return dict(wheel=Path(path).name,wheel_SHA256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                    kernel=names[0],kernel_SHA256=hashlib.sha256(data).hexdigest(),**inspect(data))

def main():
    p=argparse.ArgumentParser();p.add_argument('wheel',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with a.output.open('x',encoding='utf-8') as stream:json.dump(wheel_info(a.wheel),stream,indent=2)
if __name__=='__main__':main()
