import time
from telemetrix_Barmaja import TelemetrixSync
TRIG,ECHO=7,6

t=TelemetrixSync(); t.sonar_config(TRIG,ECHO); t.i2c_init(addr=0x27); t.lcd_print(0,0,'Distance (cm)')
while True:
    d=t.sonar_read(TRIG)
    if d is not None:
        t.lcd_print(1,0,'                ')
        t.lcd_print(1,0,f'{d:5.1f}')
        print('cm:',d)
    time.sleep(0.3)
