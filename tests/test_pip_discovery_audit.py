import struct,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_pip_discovery import audit
from pip_displaysink import subscription

def capture(body):
    udp=struct.pack('>HHHH',30490,30490,8+len(body),0)+body
    ip=bytes.fromhex('4500')+struct.pack('>H',20+len(udp))+bytes(4)+bytes([64,17])+bytes(2)+bytes([160,48,199,119,160,48,199,96])+udp
    packet=bytes(12)+bytes.fromhex('0800')+ip
    return bytes.fromhex('d4c3b2a1')+struct.pack('<HHiIII',2,4,0,0,65535,1)+struct.pack('<IIII',1,0,len(packet),len(packet))+packet
class Tests(unittest.TestCase):
    def read(self,raw):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'x.pcap';p.write_bytes(raw);return audit(p)
    def test_renewal_and_unsubscribe_distinct(self):
        for ttl in (0,3):
            r=self.read(capture(subscription('160.48.199.119',65497,1,ttl)))
            self.assertEqual(r['events'][0]['ttl'],ttl)
            self.assertEqual(r['events'][0]['port'],65497)
    def test_truncation_rejected(self):
        with self.assertRaises(ValueError):self.read(capture(subscription('160.48.199.119',65497,1))[:-1])
    def test_bad_entry_length_rejected(self):
        p=bytearray(subscription('160.48.199.119',65497,1));p[23]=17
        with self.assertRaises(ValueError):self.read(capture(p))
if __name__=='__main__':unittest.main()
