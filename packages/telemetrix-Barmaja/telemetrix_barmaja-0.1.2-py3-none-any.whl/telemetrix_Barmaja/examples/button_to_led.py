
"""Mirror a push-button to LED (INPUT_PULLUP)."""
import time
from telemetrix_Barmaja import TelemetrixSync, OUTPUT, INPUT_PULLUP, HIGH, LOW

board = TelemetrixSync()
LED, BTN = 13, 2
board.pinMode(LED, OUTPUT)
board.pinMode(BTN, INPUT_PULLUP)   # reads HIGH idle, LOW when pressed

try:
    while True:
        pressed = (board.digitalRead(BTN) == LOW)  # active LOW
        board.digitalWrite(LED, HIGH if pressed else LOW)
        time.sleep(0.02)
finally:
    board.shutdown()
