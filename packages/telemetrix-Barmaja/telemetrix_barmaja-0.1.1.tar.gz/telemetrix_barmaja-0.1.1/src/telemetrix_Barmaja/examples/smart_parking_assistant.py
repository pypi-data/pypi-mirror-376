# smart_parking_assistant.py
import time
from telemetrix_Barmaja import TelemetrixSync
TRIG,ECHO=7,6; BUZZER=8; LED=13; LCD_ADDR=0x27; CLOSE_CM=20.0
def period_for_distance(cm):
    if cm is None: return 0.8
    cm=max(5.0,min(200.0,cm)); return 0.08 + (0.8-0.08)*((cm-5.0)/(200.0-5.0))
t=TelemetrixSync(); t.sonar_config(TRIG,ECHO); t.set_output(BUZZER); t.set_output(LED); t.i2c_init(addr=LCD_ADDR); t.lcd_print(0,0,"Parking Assist")
try:
    while True:
        d=t.sonar_read(TRIG)
        if d is not None:
            t.lcd_print(1,0," "*16); t.lcd_print(1,0,f"{d:5.1f} cm")
        t.digital_write(LED, 1 if (d is not None and d<CLOSE_CM) else 0)
        per=period_for_distance(d); t.digital_write(BUZZER,1); time.sleep(0.05); t.digital_write(BUZZER,0); time.sleep(max(0.0,per-0.05))
except KeyboardInterrupt:
    t.digital_write(BUZZER,0); t.digital_write(LED,0); t.shutdown()
