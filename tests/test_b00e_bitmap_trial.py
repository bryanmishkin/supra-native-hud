import sys,struct,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from b00e_bitmap_trial import Trial,RID
from b00e_carousel import encode
from b00e_entertainment import encode as encode_ent
from ric_rle32 import marker_bgra
RESTORE=encode(100,0x6d,0x1c,0,[[0x07000029,0xffffffff,0xffffffff,0xffffffff]],b'\0\1\0')
class TrialTests(unittest.TestCase):
    def run_case(self,fail_method=None,busy=False,interrupt=False,restore=RESTORE,row=None,column=None):
        calls=[];allocated=False;failed=False
        def exchange(packet,timeout):
            nonlocal allocated,failed
            h=struct.unpack('>HHIHHBBBB',packet[:16]);m=h[1];b=packet[16:];calls.append((m,b))
            if m==3:allocated=True
            if m==8:allocated=False
            if m==fail_method and not failed:
                failed=True;raise TimeoutError('Injected lost ACK')
            reply=bytes([int(busy or (allocated and int.from_bytes(b[4:8],'big')==RID))]) if m==2 else b''
            return struct.pack('>HHIHHBBBB',h[0],m,len(reply)+8,h[3],h[4],1,1,0x80,0)+reply
        def observe(t):
            if interrupt:raise KeyboardInterrupt()
            self.assertTrue(t.present(RID))
        r=Trial(exchange,restore,lambda r:None,observe,row=row,column=column).run(marker_bgra(36,36),36,36)
        return r,calls
    def test_entertainment_focus_and_exact_restore(self):
        restore=encode_ent(100,0x66,0x16,[0]*6,0xffffffff,[[[0x07000001,0],[0x03000001,0]]],[0xffffffff]*4)
        r,c=self.run_case(restore=restore,row=0,column=1)
        self.assertTrue(r['protocol_cleanup_ok'])
        self.assertEqual(r['model_id'],0x66)
        focus_bodies=[b for m,b in c if m==9]
        self.assertEqual(focus_bodies[0][-4:],struct.pack('>I',0x66))
        self.assertLess(next(i for i,(m,b) in enumerate(c) if m==11 and b==restore),next(i for i,(m,b) in enumerate(c) if m==8))
    def test_entertainment_requires_explicit_existing_cell(self):
        restore=encode_ent(100,0x66,0x16,[0]*6,0xffffffff,[[[0x07000001,0],[0x03000001,0]]],[0xffffffff]*4)
        with self.assertRaises(ValueError):self.run_case(restore=restore)
        with self.assertRaises(ValueError):self.run_case(restore=restore,row=0,column=0)
    def test_exact_restore_before_delete(self):
        r,c=self.run_case();self.assertTrue(r['protocol_cleanup_ok']);self.assertFalse(r['visual_pass'])
        restore=next(i for i,(m,b) in enumerate(c) if m==11 and b==RESTORE)
        delete=next(i for i,(m,b) in enumerate(c) if m==8)
        self.assertLess(restore,delete);self.assertEqual(c[delete][1],struct.pack('>II',100,RID))
        self.assertFalse(any(m in (1,7) for m,b in c))
    def test_busy_pool_never_writes(self):
        r,c=self.run_case(busy=True);self.assertTrue(all(m==2 for m,b in c));self.assertFalse(r['protocol_cleanup_ok'])
    def test_lost_upload_ack_is_still_tracked(self):
        r,c=self.run_case(fail_method=3);self.assertTrue(any(m==8 for m,b in c));self.assertFalse(any(m==11 for m,b in c))
    def test_uncertain_restore_retains_image(self):
        calls=[];allocated=False
        def exchange(p,timeout):
            nonlocal allocated
            h=struct.unpack('>HHIHHBBBB',p[:16]);m=h[1];b=p[16:];calls.append((m,b))
            if m==3:allocated=True
            if m==11 and b==RESTORE:raise TimeoutError('Restore uncertain')
            body=bytes([int(allocated and int.from_bytes(b[4:8],'big')==RID)]) if m==2 else b''
            return struct.pack('>HHIHHBBBB',h[0],m,len(body)+8,h[3],h[4],1,1,0x80,0)+body
        r=Trial(exchange,RESTORE,lambda r:None,lambda t:None).run(marker_bgra(36,36),36,36)
        self.assertTrue(r['retained_bitmap_due_to_uncertain_detachment']);self.assertFalse(any(m==8 for m,b in calls))
    def test_cancel_cleans(self):
        r,c=self.run_case(interrupt=True);self.assertTrue(r['protocol_cleanup_ok']);self.assertEqual(r['status'],'failed_or_interrupted')
    def test_restore_cannot_reintroduce_test_slot(self):
        for field in range(4):
            refs=[0xffffffff]*4;refs[field]=RID
            b=encode(100,0x6d,0x1c,0,[refs],b'\0'*3)
            with self.assertRaises(ValueError):Trial(lambda *a:self.fail('No IO'),b,lambda r:None,lambda t:None)
    def test_wrong_snapshot_rejected_before_io(self):
        b=encode(100,0x6e,0x2f,0,[],b'\0'*3)
        with self.assertRaises(ValueError):Trial(lambda *a:self.fail('No IO'),b,lambda r:None,lambda t:None)
if __name__=='__main__':unittest.main()
