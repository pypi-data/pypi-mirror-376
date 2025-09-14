
"""Turn LED on in the dark using LDR on A0."""
import time
from telemetrix_Barmaja import TelemetrixSync, OUTPUT, HIGH, LOW, A0

board = TelemetrixSync()
LED = 13
THRESH = 600  # adjust to your room
board.pinMode(LED, OUTPUT)

try:
    while True:
        val = board.analogRead(A0)  # 0..1023
        board.digitalWrite(LED, HIGH if val < THRESH else LOW)
        time.sleep(0.05)
finally:
    board.digitalWrite(LED, LOW)
    board.shutdown()
