import time
from telemetrix_Barmaja import TelemetrixSync

R,G,B = 11,10,9

t = TelemetrixSync();
for p in (R,G,B): t.pwm_write(p,0)

def setRGB(r,g,b):
    t.pwm_write(R,r); t.pwm_write(G,g); t.pwm_write(B,b)

print('RGB PWM cycle')
while True:
    setRGB(255,0,0); time.sleep(0.7)
    setRGB(0,255,0); time.sleep(0.7)
    setRGB(0,0,255); time.sleep(0.7)
    setRGB(255,255,0); time.sleep(0.7)
    setRGB(0,255,255); time.sleep(0.7)
    setRGB(255,0,255); time.sleep(0.7)
