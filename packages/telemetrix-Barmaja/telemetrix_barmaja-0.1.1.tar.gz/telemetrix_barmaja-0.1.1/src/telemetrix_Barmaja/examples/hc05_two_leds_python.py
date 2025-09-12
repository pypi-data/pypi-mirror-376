# hc05_two_leds_python.py
# -----------------------------------------------------------
# FULL PYTHON solution (no .ino): Phone -> HC-05 -> PC(USB-UART) -> Python -> Arduino (Telemetrix)
#
# Architecture:
#   - HC-05 is powered and wired to a USB-UART adapter plugged into the PC.
#       HC-05 VCC -> 5V, GND -> GND
#       HC-05 TXD -> USB-UART RX
#       HC-05 RXD -> USB-UART TX (use a resistor divider to ~3.3V if possible)
#   - Phone connects to HC-05 via Bluetooth (SPP). Use any terminal app.
#   - Python opens the USB-UART COM port and reads commands from phone.
#   - Python uses telemetrix_lite to control the Arduino over USB (Telemetrix firmware).
#
# Commands (case-insensitive) to send from phone app:
#   1ON / 1OFF   -> LED1 on/off
#   2ON / 2OFF   -> LED2 on/off
#   ALLON / ALLOFF
#   STATE?       -> replies with current LED states (L1=0/1 L2=0/1)
#
# Requirements:
#   pip install telemetrix telemetrix-lite pyserial
#   Flash Arduino with Telemetrix4Arduino.ino once.
# -----------------------------------------------------------

import time
import serial
from telemetrix_Barmaja import TelemetrixSync

# ----- SETTINGS -----
HC05_PORT = "COM8"   # <-- change to your USB-UART port that is wired to HC-05 (e.g., COM7 or /dev/ttyUSB0)
BAUD = 9600

LED1 = 8
LED2 = 9

def send_line(ser, text):
    if not text.endswith("\n"):
        text += "\n"
    ser.write(text.encode())

def main():
    # 1) Connect to Arduino via telemetrix_Barmaja
    t = TelemetrixSync()
    t.set_output(LED1)
    t.set_output(LED2)
    t.digital_write(LED1, 0); t.digital_write(LED2, 0)

    # 2) Open serial to HC-05 (via USB-UART)
    print(f"Opening HC-05 serial on {HC05_PORT} @ {BAUD} ...")
    with serial.Serial(HC05_PORT, BAUD, timeout=1) as bt:
        send_line(bt, "OK Ready: 1ON/1OFF 2ON/2OFF ALLON/ALLOFF STATE?")
        buf = ""
        try:
            while True:
                # Read incoming characters from phone
                ch = bt.read(1).decode(errors="ignore")
                if ch:
                    if ch in "\r\n":
                        cmd = buf.strip().upper()
                        buf = ""
                        if not cmd:
                            continue
                        # Handle commands
                        if cmd == "1ON":
                            t.digital_write(LED1, 1); send_line(bt, "OK L1=1")
                        elif cmd == "1OFF":
                            t.digital_write(LED1, 0); send_line(bt, "OK L1=0")
                        elif cmd == "2ON":
                            t.digital_write(LED2, 1); send_line(bt, "OK L2=1")
                        elif cmd == "2OFF":
                            t.digital_write(LED2, 0); send_line(bt, "OK L2=0")
                        elif cmd == "ALLON":
                            t.digital_write(LED1, 1); t.digital_write(LED2, 1); send_line(bt, "OK L1=1 L2=1")
                        elif cmd == "ALLOFF":
                            t.digital_write(LED1, 0); t.digital_write(LED2, 0); send_line(bt, "OK L1=0 L2=0")
                        elif cmd in ("STATE?", "STATE"):
                            l1 = 1 if t.digital_read(LED1, 0) else 0
                            l2 = 1 if t.digital_read(LED2, 0) else 0
                            send_line(bt, f"STATE L1={l1} L2={l2}")
                        else:
                            send_line(bt, f"ERR Unknown: {cmd}")
                    else:
                        buf += ch
                        if len(buf) > 64:
                            buf = ""
                # small sleep to reduce CPU
                time.sleep(0.002)
        except KeyboardInterrupt:
            pass
        finally:
            t.shutdown()
            send_line(bt, "BYE")

if __name__ == "__main__":
    main()
