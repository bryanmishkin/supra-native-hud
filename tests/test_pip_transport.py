"""Real loopback TCP/UDP tests of the native transport, never a vehicle simulator."""
import pathlib, socket, struct, subprocess, sys, tempfile, time, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from pip_displaysink import discovery, completion

def acknowledgment(packet, ttl=3):
    p=bytearray(packet);p[24]=7;p[27]=0;p[33:36]=ttl.to_bytes(3,'big')
    p[40:]=bytes(4);struct.pack_into('>I',p,4,36);return bytes(p)

def event(selection=1):
    return struct.pack('>HHIHHBBBBdHHB',0xb009,0x8001,21,0,0,1,1,2,0,1.,460,237,selection)

class Transport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.exe=pathlib.Path(cls.temp.name)/'transport'
        subprocess.run(['c++','-std=c++98','-Wall','-Wextra','-Werror','-I'+str(ROOT/'tools/pip/include'),str(ROOT/'tests/pip_transport_loopback.cpp'),'-o',str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.tcp=socket.socket();self.tcp.bind(('127.0.0.1',0));self.tcp.listen();self.tcp.settimeout(3)
        self.udp=socket.socket(type=socket.SOCK_DGRAM);self.udp.bind(('127.0.0.1',0));self.udp.settimeout(4)
        self.proc=subprocess.Popen([str(self.exe),str(self.tcp.getsockname()[1]),str(self.udp.getsockname()[1]),'5'],stdout=subprocess.PIPE,text=True)
        self.conn,self.addr=self.tcp.accept();self.conn.settimeout(2)
        self.sub,self.sender=self.udp.recvfrom(2048)
        row=discovery(self.sub);self.assertEqual((row['ip'],row['port']),self.addr)
        self.assertEqual(row['ttl'],3)
    def tearDown(self):
        if self.proc.poll() is None:self.proc.terminate()
        self.proc.communicate(timeout=2)
        self.conn.close();self.tcp.close();self.udp.close()
    def receive_exact(self,n):
        out=b''
        while len(out)<n:
            part=self.conn.recv(n-len(out))
            if not part:break
            out+=part
        return out
    def unsubscribe(self):
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            p,_=self.udp.recvfrom(2048)
            if discovery(p)['ttl']==0:return
        self.fail('missing unsubscribe')
    def test_fragmentation_renewal_and_peer_disconnect(self):
        self.udp.sendto(acknowledgment(self.sub),self.sender)
        cookie=bytes.fromhex('ffff800000000008deadbeef01010200')
        for byte in cookie+event():self.conn.sendall(bytes([byte]))
        self.assertEqual(self.receive_exact(18),completion(1))
        renewal,sender=self.udp.recvfrom(2048)
        self.assertEqual(discovery(renewal)['port'],self.addr[1]);self.assertEqual(discovery(renewal)['session'],2)
        self.udp.sendto(acknowledgment(renewal),sender)
        self.conn.shutdown(socket.SHUT_RDWR);self.unsubscribe()
        stdout,_=self.proc.communicate(timeout=2);self.assertIn('NEGOTIATED_CLUSTER',stdout)
    def test_selection_before_ack(self):
        self.conn.sendall(event());time.sleep(.05)
        self.udp.sendto(acknowledgment(self.sub),self.sender)
        self.assertEqual(self.receive_exact(18),completion(1))
        self.conn.shutdown(socket.SHUT_RDWR);self.unsubscribe()
    def test_unknown_hud_selection_not_acknowledged(self):
        self.udp.sendto(acknowledgment(self.sub),self.sender);self.conn.sendall(event(0))
        self.assertEqual(self.receive_exact(18),b'');self.unsubscribe()
        self.assertNotIn('NEGOTIATED_CLUSTER',self.proc.communicate(timeout=2)[0])
    def test_spoofed_ack_cannot_grant_lease(self):
        with socket.socket(type=socket.SOCK_DGRAM) as other:other.sendto(acknowledgment(self.sub),self.sender)
        self.conn.sendall(event());self.conn.settimeout(.15)
        with self.assertRaises(socket.timeout):self.conn.recv(18)
        self.udp.sendto(acknowledgment(self.sub),self.sender)
        self.conn.settimeout(2);self.assertEqual(self.receive_exact(18),completion(1))
        self.conn.shutdown(socket.SHUT_RDWR);self.unsubscribe()
    def test_negative_ack_closes(self):
        self.udp.sendto(acknowledgment(self.sub,0),self.sender)
        self.assertEqual(self.receive_exact(18),b'');self.unsubscribe()
    def test_expired_lease_closes_without_renewal_ack(self):
        self.udp.sendto(acknowledgment(self.sub,1),self.sender);self.conn.sendall(event())
        self.assertEqual(self.receive_exact(18),completion(1))
        self.assertEqual(self.receive_exact(18),b'');self.unsubscribe()
    def test_oversized_frame_closes(self):
        p=bytearray(event());struct.pack_into('>I',p,4,0xffffffff);self.conn.sendall(p)
        self.assertEqual(self.receive_exact(18),b'');self.unsubscribe()

    def test_wrong_group_ack_closes_without_completion(self):
        bad=bytearray(acknowledgment(self.sub));bad[39]=2
        self.udp.sendto(bad,self.sender)
        self.assertEqual(self.receive_exact(18),b'');self.unsubscribe()
    def test_no_ack_is_bounded_and_unsubscribes(self):
        self.conn.sendall(event())
        self.conn.settimeout(6)
        self.assertEqual(self.receive_exact(18),b'');self.unsubscribe()
        self.assertNotIn('NEGOTIATED_CLUSTER',self.proc.communicate(timeout=2)[0])
    def test_partial_frame_peer_close_does_not_complete(self):
        self.udp.sendto(acknowledgment(self.sub),self.sender)
        self.conn.sendall(event()[:20]);self.conn.shutdown(socket.SHUT_WR)
        try:self.assertEqual(self.receive_exact(18),b'')
        except ConnectionResetError:pass # Closing a socket with unread partial data may reset it.
        self.unsubscribe()
        self.assertNotIn('NEGOTIATED_CLUSTER',self.proc.communicate(timeout=2)[0])

if __name__=='__main__':unittest.main()
