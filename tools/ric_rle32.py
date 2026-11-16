"""NBT RLE32 byte stream derived from NavigationFully's CRLE32Compressor.

Input is tightly packed BGRA. Output tuples are count then A,R,G,B.
Literal counts 1..127; repeat counts use bit7 and a 1..127 count.
Factory output always flushes to the NEXT eight-byte boundary with zeroes.
No PNG header, dimension header, or per-row reset is emitted.
"""
def encode_bgra(raw):
    if not isinstance(raw,bytes) or not raw or len(raw)%4 or len(raw)>512*512*4:
        raise ValueError('Expected bounded nonempty BGRA pixels')
    pixels=[raw[i:i+4][::-1] for i in range(0,len(raw),4)]
    output=bytearray();literal=[]
    def flush():
        if literal:
            output.append(len(literal));output.extend(b''.join(literal));literal.clear()
    i=0
    while i<len(pixels):
        run=1
        while i+run<len(pixels) and pixels[i+run]==pixels[i] and run<127:run+=1
        if run>1:
            flush();output.append(0x80|run);output.extend(pixels[i])
        elif i==len(pixels)-1:
            # Factory final single pixel flushes buffered literals separately.
            flush();output.append(1);output.extend(pixels[i])
        else:
            literal.append(pixels[i])
            if len(literal)==127:flush()
        i+=run
    flush();output.extend(b'\0'*(8-len(output)%8))
    return bytes(output)


def decode_bgra(data,pixel_count):
    if not isinstance(data,bytes) or not 1<=pixel_count<=512*512:
        raise ValueError('Invalid RLE input')
    out=bytearray();i=0
    while len(out)<pixel_count*4:
        if i>=len(data):raise ValueError('Truncated tuple')
        tag=data[i];i+=1;n=tag&127
        if n==0 or len(out)//4+n>pixel_count:raise ValueError('Invalid tuple length')
        size=4 if tag&128 else 4*n
        payload=data[i:i+size];i+=size
        if len(payload)!=size:raise ValueError('Truncated pixels')
        if tag&128:out.extend(payload[::-1]*n)
        else:
            for j in range(0,size,4):out.extend(payload[j:j+4][::-1])
    padding=8-i%8
    if len(data)!=i+padding or any(data[i:]):raise ValueError('Invalid factory padding')
    return bytes(out)


def marker_bgra(width=150,height=36):
    if not 8<=width<=512 or not 8<=height<=512:raise ValueError('Invalid dimensions')
    out=bytearray()
    for y in range(height):
        for x in range(width):
            lit=((x in (3,width-4) and 3<=y<=height-4) or
                 (y in (3,height-4) and 3<=x<=width-4) or
                 (abs(x-width//2)<=1 and 8<=y<=height-9) or
                 (abs(y-height//2)<=1 and width//3<=x<=2*width//3))
            out.extend(b'\xff\xff\xff\xff' if lit else b'\0\0\0\xff')
    return bytes(out)
