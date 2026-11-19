"""Opaque, asymmetric pixel rulers for bounded B00E geometry measurements.
Dimensions are image inputs, never claims about receiver or optical resolution.
"""
SIZES = ((36,36),(64,64),(96,96),(128,128),(128,36),(128,64),(64,128))

def validate_size(width,height):
    if type(width) is not int or type(height) is not int or (width,height) not in SIZES:
        raise ValueError('Unsupported bounded canvas dimensions')

def ruler(width,height):
    validate_size(width,height)
    out=bytearray(bytes((0,0,0,255))*(width*height))
    def pixel(x,y,color):
        if 0<=x<width and 0<=y<height:
            out[4*(y*width+x):4*(y*width+x)+4]=bytes((*color,255))
    # BGRA: four differently colored edges identify rotation and clipping.
    for x in range(width):
        pixel(x,0,(255,255,0));pixel(x,height-1,(0,128,255))
    for y in range(height):
        pixel(0,y,(0,255,0));pixel(width-1,y,(255,0,255))
    for x in range(8,width-1,8):
        for y in range(1,5):pixel(x,y,(255,255,255))
    for y in range(8,height-1,8):
        for x in range(1,5):pixel(x,y,(255,255,255))
    for x in range(width//2-5,width//2+6):pixel(x,height//2,(255,255,255))
    for y in range(height//2-5,height//2+6):pixel(width//2,y,(255,255,255))
    # Unequal corner blocks distinguish genuine image from a factory outline.
    for x in range(7,12):
        for y in range(7,10):pixel(x,y,(255,255,0))
    for x in range(width-14,width-7):
        for y in range(height-12,height-7):pixel(x,y,(0,128,255))
    return bytes(out)
