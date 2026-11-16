import struct,unittest
from capture_evidence import assess
from test_extract_pcap import packet,pcap,extract
class EvidenceTests(unittest.TestCase):
    def test_no_create_is_not_startup(self):
        b=struct.pack('>HHIHHBBBB',0xb009,1,10,1,0,1,1,1,0)+bytes(2)
        r=assess(extract(pcap(packet(0,b))))
        self.assertEqual(r['matched_guidance_create'],0);self.assertFalse(r['startup_covered']);self.assertFalse(r['independent_surface_proven']);self.assertEqual(r['events'][0]['packet_time_min_us'],1000000)
    def test_matched_create_still_not_ownership(self):
        b=struct.pack('>HHIHHBBBB',0xb006,1,8,1,1,1,1,0,0)
        s=extract(pcap(packet(0,b)))['streams'][0]
        reply=dict(s);reply['flow']=[s['flow'][2],s['flow'][3],s['flow'][0],s['flow'][1]];reply['data']=b[:14]+bytes([128,0])
        r=assess({'streams':[s,reply]});self.assertEqual(r['matched_guidance_create'],1);self.assertFalse(r['independent_surface_proven']);self.assertFalse(r['startup_covered'])
    def test_unparsed_stream_is_incomplete(self):
        r=assess(extract(pcap(packet(0,b'bad'))));self.assertFalse(r['all_streams_parse'])
