# dht11_fan_serial_bridge.py
# Reads 'TEMP:<C>' lines from an Arduino DHT11 sketch over Serial and drives a PWM fan via Telemetrix.
import time, serial
from telemetrix_Barmaja import TelemetrixSync
SERIAL_PORT="COM7"; BAUD=9600; FAN=9; MIN_C,MAX_C=20.0,40.0
def map_temp_to_pwm(c):
    c=max(MIN_C,min(MAX_C,c)); return int(((c-MIN_C)/(MAX_C-MIN_C))*255)
t=TelemetrixSync(); t.set_output(FAN)
with serial.Serial(SERIAL_PORT,BAUD,timeout=1) as ser:
    try:
        while True:
            line=ser.readline().decode(errors='ignore').strip()
            if line.startswith("TEMP:"):
                try:
                    c=float(line.split(":",1)[1]); pwm=map_temp_to_pwm(c)
                    t.pwm_write(FAN,pwm); print(f"T={c:.1f}C -> PWM {pwm}")
                except: pass
            time.sleep(0.05)
    except KeyboardInterrupt:
        t.pwm_write(FAN,0); t.shutdown()
