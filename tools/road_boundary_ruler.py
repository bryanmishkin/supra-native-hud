"""Static two-tile boundary ruler. Source columns are not screen coordinates."""
def tile(index):
    if index not in (0,1):raise ValueError('Two tiles only')
    pixels=bytearray()
    for y in range(36):
        for x in range(150):
            gx=index*150+x
            color=(0,0,0,255)
            if y in (0,35):color=(255,255,255,255)
            if gx%10==0 and (y<7 or y>28):color=(255,255,255,255)
            if gx%50==0:color=(0,180,255,255)
            if gx==0:color=(255,200,0,255)
            if gx==299:color=(0,255,0,255)
            if gx in (149,150):color=(255,0,255,255)
            # Distinct interior baselines distinguish two strips and rotation.
            if y==(12 if index==0 else 23):color=(255,200,0,255) if index==0 else (0,180,255,255)
            pixels.extend(color)
    return bytes(pixels)
