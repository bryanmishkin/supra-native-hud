"""Malformed captures must not become fabricated receiver offers."""
import struct
import unittest
import tempfile
from pathlib import Path
from audit_hud_udp import datagrams, messages, sd_entries, offered_endpoints, audit


def message(body=b'',service=0xffff,method=0x8100):
    return struct.pack('>HHIHHBBBB',service,method,8+len(body),0,1,1,1,2,0)+body


def capture(payload,fragment=0):
    udp=struct.pack('>HHHH',30490,30490,8+len(payload),0)+payload
    ip=struct.pack('>BBHHHBBH4s4s',0x45,0,20+len(udp),0,fragment,64,17,0,b'\x0a\0\0\1',b'\xef\0\0\1')+udp
    frame=bytes(12)+b'\x08\0'+ip
    return b'\xd4\xc3\xb2\xa1'+struct.pack('<HHiIII',2,4,0,0,65535,1)+struct.pack('<IIII',1,20,len(frame),len(frame))+frame


def discovery(index=0):
    entry=bytes([1,index,0,0x10])+struct.pack('>HH',0xb006,1)+bytes([1,0,0,3])+bytes(4)
    option=struct.pack('>HBB4sBBH',9,4,0,b'\x0a\0\0\2',0,6,30502)
    return bytes(4)+struct.pack('>I',16)+entry+struct.pack('>I',len(option))+option


class UdpAuditTests(unittest.TestCase):
    def test_offer_survives_full_capture(self):
        d=list(datagrams(capture(message(discovery()))))
        self.assertEqual(d[0]['time_us'],1000020)
        e=sd_entries(messages(d[0]['data'])[0]['body'])[0]
        self.assertEqual((e['service'],e['instance'],e['ttl']),(0xb006,1,3))
        self.assertEqual(e['options'],[dict(type=4,address='10.0.0.2',protocol=6,port=30502)])

    def test_concatenation_preserves_message_boundaries(self):
        m=messages(message(b'one',1,2)+message(b'two',3,4))
        self.assertEqual([(r['service'],r['body'])for r in m],[(1,b'one'),(3,b'two')])

    def test_capture_truncation_and_fragment_fail(self):
        for raw in [capture(b'x')[:-1],capture(b'x',0x2000),capture(b'x',1)]:
            with self.assertRaises(ValueError):list(datagrams(raw))

    def test_someip_truncation_and_unsupported_tp_fail(self):
        tp=bytearray(message());tp[14]=0x22
        for raw in [message(b'x')[:-1],message()+b'x',bytes(tp),b'']:
            with self.assertRaises(ValueError):messages(raw)

    def test_sd_invalid_option_references_and_extents_fail(self):
        for raw in [discovery(1),discovery()[:-1],discovery()+b'x']:
            with self.assertRaises(ValueError):sd_entries(raw)

    def test_inventory_excludes_stops_and_subscriptions(self):
        e=sd_entries(discovery())[0]
        rows=[dict(entry=e),dict(entry=dict(e,ttl=0,service=7)),dict(entry=dict(e,type=6,service=8))]
        endpoints=offered_endpoints(rows)
        self.assertEqual(endpoints[0]['services'],[dict(service=0xb006,instance=1,major=1)])

    def test_corpus_deduplicates_and_retains_packet_provenance(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ['first.pcap','duplicate.pcap']:
                (root/name).write_bytes(capture(message(discovery())))
            result=audit(root)
        self.assertEqual(result['summary'],dict(unique_captures=1,udp_datagrams=1))
        self.assertEqual(result['discovery'][0]['count'],1)
        self.assertEqual(result['discovery'][0]['first_evidence']['packet'],1)
        self.assertEqual(result['offered_endpoints'][0]['port'],30502)

    def test_stop_offer_not_promoted_to_live_offer(self):
        raw=bytearray(discovery());raw[17:20]=bytes(3)
        self.assertEqual(sd_entries(raw)[0]['ttl'],0)

if __name__=='__main__':unittest.main()
