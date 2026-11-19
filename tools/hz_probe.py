"""Synthetic numbered frames and monotonic scheduler for parked rate tests."""
import time
DIGITS=('111101101101111','010110010010111','111001111100111','111001111001111','101101111001001','111100111001111','111100111101111','111001001001001','111101111101111','111101111001111')
def frame(sequence):
    if type(sequence) is not int or not 0<=sequence<1000000:raise ValueError('Invalid frame number')
    w,h=150,36;raw=bytearray(b'\0\0\0\xff'*(w*h))
    def rect(x,y,dx,dy):
        for yy in range(y,y+dy):
            for xx in range(x,x+dx):raw[(yy*w+xx)*4:(yy*w+xx+1)*4]=b'\xff'*4
    for n,d in enumerate(f'{sequence:06d}'):
        for y in range(5):
            for x in range(3):
                if DIGITS[int(d)][y*3+x]=='1':rect(37+n*13+x*3,4+y*3,3,3)
    gray=(sequence^(sequence>>1))&0xffff
    for bit in range(16):
        if gray&(1<<(15-bit)):rect(11+8*bit,27,6,6)
    return bytes(raw)

def run(hz,seconds,publish,record,clock=time.monotonic,sleep=time.sleep):
    if type(hz) is not int or not 1<=hz<=60:raise ValueError('Unsupported staged rate')
    if seconds not in (30,120):raise ValueError('Expected short sweep or confirmation window')
    origin=clock();rows=[];period=1/hz
    for seq in range(1,hz*seconds+1):
        scheduled=origin+(seq-1)*period
        sleep(max(0,scheduled-clock()))
        started=clock()
        if started-scheduled>period:raise RuntimeError('Scheduler fell a full frame behind; stop rate escalation')
        posted=publish(seq)
        completed=clock()
        row=dict(sequence=seq,scheduled=scheduled,started=started,posted=posted,completed=completed,cycle_seconds=completed-started,missed_period=completed>scheduled+period)
        rows.append(row);record(rows)
        if row['missed_period']:raise RuntimeError('Complete frame transaction exceeded requested period')
    sleep(max(0,origin+seconds-clock()))
    return rows
