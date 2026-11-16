import unittest,struct,sys,copy,json,hashlib,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ric_resource_check import decode_check_packet,encode_check_body,encode_distinct_create_body
from ric_lifecycle import decode_body
from ric_exchange_audit import correlate,audit_inventory

def packet(body,kind=0,code=0,session=2):
    return struct.pack('>HHIHHBBBB',0xb006,2,len(body)+8,1,session,1,1,kind,code)+body

def pair():
    return [dict(flow=['a',10,'b',20],timestamp_us=100,decoded=decode_check_packet(packet(bytes.fromhex('01020304 11121314 02')))),dict(flow=['b',20,'a',10],timestamp_us=101,decoded=decode_check_packet(packet(b'\0',0x80)))]

class ResourceCheckTests(unittest.TestCase):
    def test_fixed_request(self):
        body=encode_check_body(0x01020304,0x11121314,2)
        self.assertEqual(body,bytes.fromhex('01020304 11121314 02'))
        self.assertEqual(decode_check_packet(packet(body))['resource_id'],0x11121314)
    def test_boolean_reply(self):
        for value in (0,1):self.assertEqual(decode_check_packet(packet(bytes([value]),0x80))['check_result'],bool(value))
        for b in (b'',b'\2',b'\0\0'):
            with self.assertRaises(ValueError):decode_check_packet(packet(b,0x80))
    def test_errors_never_become_false(self):
        for kind,code in ((0x80,1),(0x81,1),(0x81,0)):
            r=decode_check_packet(packet(b'',kind,code));self.assertIsNone(r['check_result']);self.assertFalse(r['remote_cleanup_proven'])
    def test_truncation(self):
        p=packet(encode_check_body(1,2,3))
        for n in range(len(p)):
            with self.assertRaises(ValueError):decode_check_packet(p[:n])
    def test_bounds(self):
        for args in ((-1,2,3),(1,2**32,3),(1,2,12),(True,2,3)):
            with self.assertRaises(ValueError):encode_check_body(*args)
    def test_create_fixed_body(self):
        body=encode_distinct_create_body(['A','B','C'],[1,2,3])
        self.assertEqual(body,bytes.fromhex('00000006 feff00410000 00000006 feff00420000 00000006 feff00430000 00000001 00000002 00000003'))
        r=decode_body(1,0,0,body);self.assertEqual(r['identity_strings'],['A','B','C']);self.assertFalse(r['independent_ownership_proven'])
    def test_create_rejects_factory_roles(self):
        for name in ('BMW.IC.Guidance','BMW.HMI.Roadbook'):
            with self.assertRaises(ValueError):encode_distinct_create_body([name,'x','y'],[3,3,1])
    def test_create_rejects_bad_identity_or_version(self):
        for names,versions in ((['','B','C'],[1,2,3]),(['é','B','C'],[1,2,3]),(['A'*511,'B','C'],[1,2,3]),(['A','B'],[1,2,3]),(['A','B','C'],[1,2]),(['A','B','C'],[True,2,3])):
            with self.assertRaises(ValueError):encode_distinct_create_body(names,versions)
    def test_unique_pair(self):
        r=correlate(pair());self.assertEqual(len(r['matched']),1);self.assertFalse(r['matched'][0]['check_result']);self.assertFalse(r['remote_cleanup_proven'])
    def test_no_join_on_other_flow_or_id(self):
        for field in ('flow','client','session'):
            rows=pair()
            if field=='flow':rows[1]['flow'][1]=99
            else:rows[1]['decoded'][field]=99
            self.assertFalse(correlate(rows)['matched'])
    def test_duplicates_unmatched(self):
        rows=pair();rows.append(copy.deepcopy(rows[0]));self.assertFalse(correlate(rows)['matched'])
    def test_timing_required(self):
        for value in (None,99):
            rows=pair();rows[1]['timestamp_us']=value;self.assertFalse(correlate(rows)['matched'])
    def test_error_correlated_but_not_absence(self):
        rows=pair();rows[1]['decoded']=decode_check_packet(packet(b'',0x81,1));self.assertIsNone(correlate(rows)['matched'][0]['check_result'])
    def test_inventory_hash_and_path_checks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=packet(encode_check_body(1,2,3));(root/'s.bin').write_bytes(data)
            entry=dict(file='s.bin',flow=['a',1,'b',2],sha256=hashlib.sha256(data).hexdigest(),byte_spans=[])
            p=root/'inventory.json';p.write_text(json.dumps({'streams':[entry]}));self.assertEqual(len(audit_inventory(p)['unresolved']),1)
            entry['sha256']='wrong';p.write_text(json.dumps({'streams':[entry]}))
            with self.assertRaises(ValueError):audit_inventory(p)
            entry['file']='../outside.bin';p.write_text(json.dumps({'streams':[entry]}))
            with self.assertRaises(ValueError):audit_inventory(p)
