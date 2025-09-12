import time
from telemetrix_Barmaja import TelemetrixSync

BTN, LED = 7, 13

t = TelemetrixSync(); t.set_input(BTN, pullup=True); t.set_output(LED)
print('Pressed=0 with INPUT_PULLUP')
while True:
    v = t.digital_read(BTN, default=1)
    if v == 0:
        t.digital_write(LED, 1)
    else:
        t.digital_write(LED, 0)
    time.sleep(0.02)
