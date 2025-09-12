import time
from telemetrix_Barmaja import TelemetrixSync

ROWS=[2,3,4,5]; COLS=[6,7,8,9]; SERVO=11; PWD='123A'
KEYS=[['1','2','3','A'],['4','5','6','B'],['7','8','9','C'],['*','0','#','D']]

t=TelemetrixSync()
for r in ROWS: t.set_output(r)
for c in COLS: t.set_input(c,pullup=True)

t.servo_write(SERVO,0)
entry=''
while True:
    key=None
    for i,r in enumerate(ROWS):
        t.digital_write(r,0); time.sleep(0.002)
        for j,c in enumerate(COLS):
            v=t.digital_read(c,default=1)
            if v==0: key=KEYS[i][j]
        t.digital_write(r,1)
    if key:
        print('key:',key)
        if key in '0123456789ABCD#*': entry+=key
        if len(entry)>8: entry=entry[-8:]
        if entry.endswith(PWD):
            print('UNLOCK!');
            for ang in (90,0): t.servo_write(SERVO,ang); time.sleep(0.6)
            entry=''
    time.sleep(0.02)
