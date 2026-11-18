import math,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from pip_displaysink import subscription,discovery,completion,Negotiation

def ack(ttl):
    p=bytearray(subscription('192.0.2.1',40000,3,ttl));p[24]=7;p[27]=0;p[40:]=bytes(4);struct.pack_into('>I',p,4,36);return bytes(p)
def event(selection=1,width=460,height=237):
    return struct.pack('>HHIHHBBBBdHHB',0xb009,0x8001,21,0,0,1,1,2,0,1.,width,height,selection)
def state():return Negotiation([(1.,460,237,1)])

class SinkTests(unittest.TestCase):
    def test_subscription_bounds_and_unsubscribe(self):
        for ttl in (0,3,30,0xffffff):
            r=discovery(subscription('192.0.2.7',45000,65535,ttl,False))
            self.assertEqual((r['ip'],r['port'],r['session'],r['ttl'],r['reboot']),('192.0.2.7',45000,65535,ttl,False))
        for ip,port,session,ttl in [('0.0.0.0',1,1,3),('239.1.1.1',1,1,3),('192.0.2.1',0,1,3),('192.0.2.1',1,0,3),('192.0.2.1',1,1,1<<24)]:
            with self.assertRaises(ValueError):subscription(ip,port,session,ttl)
    def test_fragmented_event_requires_actual_send_and_live_lease(self):
        s=state();s.ack(ack(3),10);p=event()
        for b in p[:-1]:self.assertEqual(s.feed(bytes([b])),[])
        answers=s.feed(p[-1:]);self.assertEqual(answers,[completion(1)]);self.assertFalse(s.negotiated(10.1))
        s.completion_sent(answers[0],10.1);self.assertTrue(s.negotiated(12.9));self.assertFalse(s.negotiated(13))
    def test_nack_and_close_remove_selection(self):
        s=state();s.ack(ack(3),10);out=s.feed(event())[0];s.completion_sent(out,10.1)
        s.ack(ack(0),11);self.assertFalse(s.negotiated(11));s.close()
        with self.assertRaises(ValueError):s.feed(event())
        with self.assertRaises(ValueError):s.ack(ack(3),12)
    def test_unknown_hud_does_not_inherit_cluster_readiness(self):
        s=state();s.ack(ack(3),10);s.completion_sent(s.feed(event())[0],10.1)
        with self.assertRaises(ValueError):s.feed(event(0,277,160))
        self.assertFalse(s.negotiated(11));self.assertTrue(s.failed)
    def test_pending_mismatch_and_expiry(self):
        s=state();s.ack(ack(3),10);s.feed(event())
        for p,t in [(completion(0),11),(completion(1),13),(completion(1),math.nan)]:
            with self.assertRaises(ValueError):s.completion_sent(p,t)
        self.assertFalse(s.negotiated(11))
    def test_invalid_and_oversized_frames_fail_closed(self):
        for p in [bytes(16),bytes(4097),event()+event()]:
            s=state()
            with self.assertRaises(ValueError):s.feed(p)
            self.assertTrue(s.failed);self.assertFalse(s.negotiated(0))
    def test_truncated_discovery_and_wrong_group(self):
        p=subscription('192.0.2.1',40000,1)
        for n in range(len(p)):
            with self.assertRaises(ValueError):discovery(p[:n])
        b=bytearray(ack(3));b[39]=2
        with self.assertRaises(ValueError):discovery(bytes(b))
