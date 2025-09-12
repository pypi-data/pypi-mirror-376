# ultrasonic_buzzer_speed.py
import time
from telemetrix_Barmaja import TelemetrixSync
TRIG,ECHO=7,6; BUZZER=8
def period_for_distance(cm):
    if cm is None: return 0.8
    cm = max(5.0, min(200.0, cm))
    return 0.08 + (0.8 - 0.08) * ((cm - 5.0) / (200.0 - 5.0))
t=TelemetrixSync(); t.sonar_config(TRIG,ECHO); t.set_output(BUZZER)
try:
    while True:
        d=t.sonar_read(TRIG); per=period_for_distance(d)
        t.digital_write(BUZZER,1); time.sleep(0.06)
        t.digital_write(BUZZER,0); time.sleep(max(0.0, per-0.06))
except KeyboardInterrupt:
    t.digital_write(BUZZER,0); t.shutdown()
