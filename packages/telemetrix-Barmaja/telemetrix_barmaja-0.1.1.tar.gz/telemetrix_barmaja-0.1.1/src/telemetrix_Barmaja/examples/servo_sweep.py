import time
from telemetrix_Barmaja import TelemetrixSync

SERVO = 9

t = TelemetrixSync(); t.servo_write(SERVO, 0)
print('Servo sweep 0..180..0')
while True:
    for ang in range(0,181,5): t.servo_write(SERVO, ang); time.sleep(0.02)
    for ang in range(180,-1,-5): t.servo_write(SERVO, ang); time.sleep(0.02)
