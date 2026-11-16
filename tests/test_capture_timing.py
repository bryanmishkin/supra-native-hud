import struct,unittest
from test_extract_pcap import packet,pcap,extract
class TimingTests(unittest.TestCase):
    def test_packet_spans_survive_reordering(self):
        msg=struct.pack('>HHIHHBBBB',0xb006,1,12,1,1,1,1,0,0)+b'abcd'
        b=bytearray(pcap(packet(8,msg[8:]),packet(0,msg[:8])))
        struct.pack_into('<II',b,24,2,125)
        second=24+16+len(packet(8,msg[8:]));struct.pack_into('<II',b,second,1,750)
        s=extract(bytes(b))['streams'][0];self.assertEqual(s['data'],msg)
        self.assertEqual([(x['offset'],x['timestamp_us'],x['packet']) for x in s['byte_spans']],[(0,1000750,2),(8,2000125,1)])
    def test_limits_are_bounded(self):
        for kw in [dict(max_bytes=65*1024*1024),dict(max_packets=65537),dict(max_packets=0)]:
            with self.assertRaises(ValueError):extract(pcap(),**kw)
if __name__=='__main__':unittest.main()
