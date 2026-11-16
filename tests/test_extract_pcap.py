import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
from extract_someip_pcap import extract

def packet(seq,body,frag=0):
    tcp=struct.pack('>HHIIBBHHH',1000,30502,seq,0,0x50,0x18,0,0,0)+body
    ip=struct.pack('>BBHHHBBH4s4s',0x45,0,20+len(tcp),0,frag,64,6,0,b'\xa0\x30\xc7\x77',b'\xa0\x30\xc7\x60')+tcp
    return bytes(12)+b'\x08\x00'+ip

def pcap(*packets):
    return struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1)+b''.join(struct.pack('<IIII',1,0,len(p),len(p))+p for p in packets)

class ExtractTests(unittest.TestCase):
    def test_reorder_retransmit_and_wrap(self):
        msg=struct.pack('>HHIHHBBBB',0xb006,10,12,1,1,1,1,0,0)+b'abcd'
        r=extract(pcap(packet(4,msg[8:]),packet(0xfffffffc,msg[:12]),packet(4,msg[8:])))
        self.assertEqual(r['streams'][0]['data'],msg)
        self.assertEqual(r['streams'][0]['inventory']['messages'],1)
    def test_gaps_conflicts_fragmentation(self):
        for data in [pcap(packet(0,b'ab'),packet(3,b'd')),pcap(packet(0,b'ab'),packet(1,b'X')),pcap(packet(0,b'a',frag=0x2000))]:
            with self.assertRaises(ValueError):extract(data)
    def test_truncated_capture(self):
        data=pcap(packet(0,b'abcd'))
        for end in range(1,len(data)):
            if end==24:continue
            with self.subTest(end=end),self.assertRaises(ValueError):extract(data[:end])
    def test_mid_message_preserved_not_guessed(self):
        s=extract(pcap(packet(20,b'incomplete')))['streams'][0]
        self.assertIsNone(s['inventory']);self.assertTrue(s['parse_error']);self.assertFalse(s['boundary_proven'])
if __name__=='__main__':unittest.main()
