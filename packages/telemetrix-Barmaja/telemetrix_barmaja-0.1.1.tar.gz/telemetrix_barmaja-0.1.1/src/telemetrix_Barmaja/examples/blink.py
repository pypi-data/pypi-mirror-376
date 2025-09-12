import time
from telemetrix_Barmaja import TelemetrixSync

t=TelemetrixSync(); t.set_output(13)
while True:
    t.digital_write(13,1); time.sleep(0.5)
    t.digital_write(13,0); time.sleep(0.5)
