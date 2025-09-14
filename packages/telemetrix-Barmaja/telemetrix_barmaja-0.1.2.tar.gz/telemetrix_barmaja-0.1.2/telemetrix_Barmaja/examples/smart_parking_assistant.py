
"""Smart parking: LED under 30 cm; buzzer beeps faster when closer."""
import time
from telemetrix_Barmaja import TelemetrixSync, OUTPUT, HIGH, LOW

board = TelemetrixSync()
TRIG, ECHO = 7, 8
LED = 13
BUZZ = 12
board.pinMode(LED, OUTPUT)
board.pinMode(BUZZ, OUTPUT)

try:
    while True:
        try:
            d = board.sonarReadCM(TRIG, ECHO)
        except RuntimeError:
            d = 999
        board.digitalWrite(LED, HIGH if d < 30 else LOW)
        gap = max(0.03, min(0.6, d/150.0))
        board.digitalWrite(BUZZ, 1); time.sleep(0.01)
        board.digitalWrite(BUZZ, 0); time.sleep(gap)
finally:
    board.digitalWrite(LED, LOW); board.digitalWrite(BUZZ, 0)
    board.shutdown()
