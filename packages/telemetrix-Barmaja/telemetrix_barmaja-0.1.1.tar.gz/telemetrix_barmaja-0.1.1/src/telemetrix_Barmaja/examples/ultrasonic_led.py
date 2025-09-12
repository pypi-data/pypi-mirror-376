# ultrasonic_led.py
import time
from telemetrix_Barmaja import TelemetrixSync
TRIG,ECHO=7,6; LED=13; THRESHOLD=25.0
t=TelemetrixSync(); t.sonar_config(TRIG,ECHO); t.set_output(LED)
try:
    while True:
        d=t.sonar_read(TRIG)
        t.digital_write(LED, 1 if (d is not None and d<THRESHOLD) else 0)
        time.sleep(0.1)
except KeyboardInterrupt:
    t.digital_write(LED,0); t.shutdown()
