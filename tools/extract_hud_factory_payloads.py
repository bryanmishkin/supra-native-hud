import sys,struct,hashlib,json,collections,zlib,argparse
from pathlib import Path
from extract_someip_pcap import extract
parser=argparse.ArgumentParser(description='Offline private payload extraction; never transmits. Output includes private text and OEM icons.')
parser.add_argument('capture_root',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
out=args.output;out.mkdir(parents=True,exist_ok=False);results={}
for phase in ('door','radio','phone','voice'):
 p=next((args.capture_root/phase).glob('recording-*/traffic.pcap'));a=extract(p.read_bytes(),max_bytes=64*1024*1024,max_packets=65536);rows=[]
 for s in a['streams']:
  if s['parse_error']:raise ValueError(s['parse_error'])
  off=0;b=s['data']
  while off<len(b):
   n=struct.unpack_from('>I',b,off+4)[0]+8;pkt=b[off:off+n];off+=n;svc,m=struct.unpack_from('>HH',pkt)
   if svc not in (0xb011,0xb00e):continue
   body=pkt[16:];texts=[]
   for i in range(len(body)-6):
    size=struct.unpack_from('>I',body,i)[0]
    if 2<=size<=2048 and size%2==0 and i+4+size<=len(body) and body[i+4:i+6]==b'\xfe\xff':
     try:texts.append({'offset':i,'text':body[i+6:i+4+size].decode('utf-16-be').rstrip('\x00')})
     except UnicodeDecodeError:pass
   row={'service':hex(svc),'method':hex(m),'kind':pkt[14],'client':struct.unpack_from('>H',pkt,8)[0],'session':struct.unpack_from('>H',pkt,10)[0],'flow':s['flow'],'body_bytes':len(body),'body_hex':body.hex(),'texts':texts}
   index=body.find(b'\x89PNG\r\n\x1a\n')
   if index>=0:
    end=index+8;chunks=[]
    while end<len(body):
     length=struct.unpack_from('>I',body,end)[0];kind=body[end+4:end+8];payload=body[end+8:end+8+length];crc=struct.unpack_from('>I',body,end+8+length)[0]
     if zlib.crc32(kind+payload)&0xffffffff!=crc:raise ValueError('PNG CRC')
     chunks.append(kind.decode());end+=12+length
     if kind==b'IEND':break
    png=body[index:end];h=hashlib.sha256(png).hexdigest();fn=h[:16]+'.png';(out/fn).write_bytes(png)
    row['png']={'file':fn,'sha256':h,'offset':index,'bytes':len(png),'dimensions':struct.unpack_from('>II',png,16),'chunks':chunks,'crc_verified':True}
   rows.append(row)
 results[phase]=rows
 print(phase,'messages',len(rows),'methods',collections.Counter((x['method'],x['kind']) for x in rows),'text_fields',sum(len(x['texts']) for x in rows))
 print('PNG',[(x['method'],x['kind'],x['png']['dimensions'],x['png']['file']) for x in rows if 'png' in x])
(out/'decoded-private.json').write_text(json.dumps(results,indent=2))
