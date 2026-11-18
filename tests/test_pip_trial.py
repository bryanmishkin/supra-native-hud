import json
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pip_trial import allocation,descriptor,detail,Session,run,measured_support,producer_contract,validate_producer
from ric_live_trial import TcpExchange
from ric_resource import decode_resource_body


def fixture():
    configs=[]
    for tag,t,count,offset in [(19,7,5,0x07000000),(17,15,5,0x0f000000),
                               (20,32,1,0x20000000),(21,33,1,0x21000000),
                               (4,17,1,0x11000000),(1,34,5,0x22000000),(18,29,30,0x1d000000)]:
        raw=struct.pack('>BBII',tag,t,count,offset)
        configs.append(struct.pack('>II',len(raw),tag)+raw)
    raw=struct.pack('>BBIIHHBB',35,2,5,0x02000000,320,320,1,0)
    configs.append(struct.pack('>II',len(raw),35)+raw)
    raw=b''.join(configs);body=struct.pack('>II',200,len(raw))+raw
    return struct.pack('>HHIHHBBBB',0xb006,1,len(body)+8,0x5350,1,1,1,128,0)+body


class TrialTests(unittest.TestCase):
    def test_descriptor(self):
        a=allocation(fixture());d=decode_resource_body(descriptor(a))
        self.assertEqual(d['resource_id'],0x02000004)
        self.assertEqual(d['picture_in_picture']['resolution_pair'],[320,200])
        self.assertFalse(d['picture_in_picture']['pixel_payload_present'])
        self.assertEqual(d['picture_in_picture']['color_depth_enum'],0)
        self.assertEqual(a['supported_depth'],1)
        b=detail(a);self.assertEqual(len(b),71)
        self.assertEqual(struct.unpack_from('>I',b,35)[0],0x02000004)
        self.assertEqual(b[8],7)

    def test_mismatched_or_old_producer_refused(self):
        a=allocation(fixture());contract=producer_contract(a)
        for key,value in [('depth',1),('description_id',0x0f000000),
                          ('metadata_id_be','0400000f'),('content',[800,480]),
                          ('packing',1),('resource_id',0x02000000)]:
            wrong=dict(contract);wrong[key]=value
            with self.assertRaises(ValueError):
                validate_producer(('PIP_BINDING '+json.dumps(wrong)+'\nPRODUCER_READY\n').encode(),a)
        for output in [b'PRODUCER_READY\n',b'PIP_BINDING {}\n']:
            with self.assertRaises(ValueError):validate_producer(output,a)

    def test_bad_profile_and_truncation(self):
        raw=fixture()
        for n in range(len(raw)):
            with self.assertRaises(ValueError):allocation(raw[:n])
        b=bytearray(raw);b[-1]=1
        with self.assertRaises(ValueError):allocation(bytes(b))

    def exercise(self,busy=False,reject=None,disconnect=None,producer_fail=False,binding_mismatch=False):
        observed=[];errors=[]
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1)
        def peer():
            try:
                conn,_=listener.accept()
                with conn:
                    conn.settimeout(5);present=busy
                    def exact(n):
                        b=b''
                        while len(b)<n:
                            v=conn.recv(n-len(b))
                            if not v:return None
                            b+=v
                        return b
                    while True:
                        h=exact(16)
                        if h is None:break
                        f=list(struct.unpack('>HHIHHBBBB',h));b=exact(f[2]-8)
                        observed.append((f[1],b));method=f[1]
                        if method==3:present=True
                        if method==8:present=False
                        if method==disconnect:return
                        answer=bytes([present]) if method==2 else b''
                        f[2]=len(answer)+8;f[7]=128;f[8]=1 if method==reject else 0
                        conn.sendall(struct.pack('>HHIHHBBBB',*f)+answer)
            except Exception as e:errors.append(e)
            finally:listener.close()
        t=threading.Thread(target=peer);t.start()
        a=allocation(fixture());snapshots=[]
        # Synthetic loopback-only support values; never packaged for a car.
        a['support_start']=[(10,struct.pack('>IIB',200,a['models'][t],t).hex()) for t in (34,29)]
        a['position_start']=a['position_stop']=struct.pack('>IIB',200,a['models'][17],17).hex()
        contract=producer_contract(a)
        if binding_mismatch:contract['depth']=1
        producer=[sys.executable,'-u','-c',
            'import time; print('+repr('PIP_BINDING '+json.dumps(contract))+'); print("PRODUCER_READY"); time.sleep(.1); print("PRODUCER_END local_cleanup=1")']
        if producer_fail:producer=[sys.executable,'-c','raise SystemExit(1)']
        with tempfile.TemporaryDirectory() as tmp:
            with socket.create_connection(listener.getsockname(),2) as conn:
                s=Session(TcpExchange(conn,tmp),a);s.timeout=.2
                result=run(s,a,producer,lambda r:snapshots.append(json.loads(json.dumps(r))))
        t.join(6);self.assertFalse(t.is_alive());self.assertFalse(errors)
        self.assertTrue(snapshots)
        self.assertTrue(all(m not in (1,7) for m,b in observed))
        self.assertTrue(all(struct.unpack_from('>I',b,4)[0]==0x02000004 for m,b in observed if m in (2,3,8)))
        return result,observed

    def test_success_cleanup_no_visual_claim(self):
        r,obs=self.exercise()
        self.assertEqual(r['status'],'finished');self.assertTrue(r['protocol_cleanup'])
        self.assertTrue(r['local_cleanup']);self.assertFalse(r['visual_pass'])
        self.assertFalse(r['resume_v1_allowed']);self.assertEqual(obs[-1][0],2)

    def test_busy_slot_no_mutation(self):
        r,obs=self.exercise(busy=True)
        self.assertEqual([m for m,b in obs],[2]);self.assertFalse(r['protocol_cleanup'])

    def test_rejected_graph_still_withdraws_and_removes(self):
        r,obs=self.exercise(reject=11)
        self.assertEqual(r['status'],'failed');self.assertIn(8,[m for m,b in obs])
        self.assertFalse(r['protocol_cleanup']) # Rejected empty-detail cleanup remains uncertain.

    def test_lost_upload_ack_never_reconnects_or_claims_clean(self):
        r,obs=self.exercise(disconnect=3)
        self.assertEqual([m for m,b in obs],[2,3]);self.assertFalse(r['protocol_cleanup'])
        self.assertFalse(r['resume_v1_allowed'])

    def test_stale_producer_cleans_descriptor_without_activating_graph(self):
        r,obs=self.exercise(binding_mismatch=True)
        self.assertFalse(r['graph_attempted']);self.assertTrue(r['protocol_cleanup'])
        self.assertEqual([m for m,b in obs],[2,3,2,8,2])
        self.assertIn('contract mismatch',r['error'])

    def test_producer_failure_removes_resource_without_graph(self):
        r,obs=self.exercise(producer_fail=True)
        self.assertFalse(r['graph_attempted']);self.assertTrue(r['protocol_cleanup'])
        self.assertFalse(r['local_cleanup']);self.assertEqual([m for m,b in obs],[2,3,2,8,2])

    def test_cannot_dispose_factory_instance_or_other_slot(self):
        a=allocation(fixture());s=Session(lambda *args:self.fail('Transport reached'),a)
        for m,b in [(7,struct.pack('>I',200)),(8,struct.pack('>II',200,0x02000000)),
                    (9,struct.pack('>IIB',200,0x21000001,33))]:
            with self.assertRaises(ValueError):s._request(m,b)

    def test_unmeasured_support_refused(self):
        with self.assertRaises(ValueError):measured_support(b'SHP1\0\x0a\0\x07',allocation(fixture()))

if __name__=='__main__':unittest.main()
