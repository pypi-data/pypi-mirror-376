# lm35_fan_pwm.py
import time
from telemetrix_Barmaja import TelemetrixSync
A0=0; FAN=9; MIN_C,MAX_C=20.0,40.0
def lm35_celsius(adc): return (adc*(5.0/1023.0))*100.0
def map_temp_to_pwm(c):
    c=max(MIN_C,min(MAX_C,c)); return int(((c-MIN_C)/(MAX_C-MIN_C))*255)
t=TelemetrixSync(); t.set_analog_input(A0); t.set_output(FAN)
try:
    while True:
        a=t.analog_read(A0,default=None)
        if a is None: time.sleep(0.05); continue
        c=lm35_celsius(a); pwm=map_temp_to_pwm(c)
        t.pwm_write(FAN,pwm); print(f"A0={a:4d} -> {c:5.1f}C -> PWM {pwm}"); time.sleep(0.2)
except KeyboardInterrupt:
    t.pwm_write(FAN,0); t.shutdown()
