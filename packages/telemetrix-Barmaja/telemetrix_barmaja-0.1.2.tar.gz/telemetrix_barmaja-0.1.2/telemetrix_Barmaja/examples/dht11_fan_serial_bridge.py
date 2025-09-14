
"""Serial bridge: Arduino prints TEMP:23; Python maps 20..40C to PWM 0..255 on pin 5."""
import time, re, serial
from telemetrix_Barmaja import TelemetrixSync, OUTPUT

ser = serial.Serial('COM6', 9600, timeout=1)  # set your COM
board = TelemetrixSync()
FAN_PWM = 5
board.pinMode(FAN_PWM, OUTPUT)

def parse_temp(line):
    m = re.search(r"TEMP\s*:\s*(\d+(?:\.\d+)?)", line)
    return float(m.group(1)) if m else None

try:
    while True:
        line = ser.readline().decode(errors='ignore').strip()
        tC = parse_temp(line)
        if tC is None:
            continue
        tC = max(20.0, min(40.0, tC))
        pwm = int((tC-20.0)/20.0*255)
        board.analogWrite(FAN_PWM, pwm)
        print(f"Temp={tC:4.1f} PWM={pwm:3d}")
finally:
    board.analogWrite(FAN_PWM, 0)
    board.shutdown()
    ser.close()
