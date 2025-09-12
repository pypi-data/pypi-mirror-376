# ultrasonic_5leds_bargraph.py
import time
from telemetrix_Barmaja import TelemetrixSync
TRIG,ECHO=7,6; LEDS=[3,4,5,8,9]; MIN_CM,MAX_CM=5.0,80.0
t=TelemetrixSync(); t.sonar_config(TRIG,ECHO)
for p in LEDS: t.set_output(p)
def level(cm):
    if cm is None: return 0
    if cm<=MIN_CM: return 5
    if cm>=MAX_CM: return 0
    frac=1.0-(cm-MIN_CM)/(MAX_CM-MIN_CM)
    return int(round(frac*5))
try:
    while True:
        d=t.sonar_read(TRIG); lvl=level(d)
        for i,p in enumerate(LEDS, start=1): t.digital_write(p, 1 if i<=lvl else 0)
        time.sleep(0.1)
except KeyboardInterrupt:
    for p in LEDS: t.digital_write(p,0); t.shutdown()
