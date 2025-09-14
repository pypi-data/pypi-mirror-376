
"""Map LDR (A0) to LED PWM (pin 5)."""
import time
from telemetrix_Barmaja import TelemetrixSync, OUTPUT, A0

board = TelemetrixSync()
LED_PWM = 5
board.pinMode(LED_PWM, OUTPUT)

try:
    while True:
        raw = board.analogRead(A0)          # 0..1023
        pwm = int(raw / 1023 * 255)         # 0..255
        board.analogWrite(LED_PWM, pwm)
        time.sleep(0.02)
finally:
    board.analogWrite(LED_PWM, 0)
    board.shutdown()
