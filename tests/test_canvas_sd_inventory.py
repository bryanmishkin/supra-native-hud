import importlib.util,pathlib,struct,unittest
src=pathlib.Path(__file__).parents[1]/'tools'/'canvas_sd_inventory.py'
spec=importlib.util.spec_from_file_location('canvassd',src)
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

def sd_message():
    entry=bytes([1,0,0,0])+struct.pack('>HHB',0xb006,1,1)+bytes([0,0,5])+struct.pack('>I',1)
    payload=bytes([0xC0,0,0,0])+struct.pack('>I',16)+entry+struct.pack('>I',0)
    return struct.pack('>HHIHHBBBB',0xffff,0x8100,len(payload)+8,0,1,1,1,2,0)+payload

def pcap(sd):
    udp=struct.pack('>HHHH',30490,30490,len(sd)+8,0)+sd
    ip=bytearray(20);ip[0]=0x45;ip[2:4]=struct.pack('>H',20+len(udp));ip[9]=17;ip[12:16]=bytes([160,48,199,119])
    frame=b'\0'*12+struct.pack('>H',0x0800)+bytes(ip)+udp
    header=b'\xd4\xc3\xb2\xa1'+struct.pack('<HHIIII',2,4,0,0,65535,1)
    return header+struct.pack('<IIII',0,0,len(frame),len(frame))+frame

class Tests(unittest.TestCase):
    def test_single_offer(self):
        d1=d.parse_sd(sd_message());self.assertEqual(d1['entries'][0]['service_id'],'0xb006')
        out=d.pcap_inventory(pcap(sd_message()));self.assertEqual(out['service_count'],1)
        self.assertEqual(out['someip_sd_packets'],1);self.assertFalse(out['graphics_surface_proven'])
    def test_fail_closed(self):
        with self.assertRaises(ValueError):d.pcap_inventory(pcap(sd_message())[:-10])
        with self.assertRaises(ValueError):d.parse_sd(sd_message()[:-1])
    def test_unrecognized_packet_not_service(self):
        data=pcap(sd_message());z=bytearray(data);z[-40]=-1&255
        result=d.pcap_inventory(bytes(z));self.assertIsInstance(result['service_count'],int)
if __name__=='__main__':unittest.main()

