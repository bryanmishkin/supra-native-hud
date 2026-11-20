"""Extent probe: retain V1's 150x36 tile and add a 64x36 end-marked tile.
No alignment changes. The 214 source columns do not imply a 214-pixel viewport.
"""

def image(index):
    if index not in (0,1):raise ValueError('Exactly two owned images')
    width=150 if index==0 else 64
    raw=bytearray()
    for y in range(36):
        for x in range(width):
            color=(0,0,0,255)
            # Keep the full V1-sized boundary as a simultaneous physical reference.
            if x in (0,width-1) or y in (0,35):
                color=(255,200,0,255) if index==0 else (0,180,255,255)
            if index==0:
                if 8<=x<142 and 12<=y<24:color=(255,200,0,255)
                if x%10==0 and y<6:color=(255,255,255,255)
            else:
                # Three spatial fiducials; the far-right green rail must be visible.
                if x in (8,32,55) and 8<=y<=27:color=(255,255,255,255)
                if y in (17,18) and 4<=x<=59:color=(255,255,255,255)
                if 60<=x<=63:color=(0,255,0,255)
            raw.extend(color)
    return width,36,bytes(raw)
