# hc05_two_leds_ldr_python.py
# -----------------------------------------------------------
# FULL PYTHON solution (no .ino): Phone -> HC-05 -> PC(USB-UART) -> Python -> Arduino (Telemetrix)
# Adds LDR (A0) readback on demand or periodic stream.
#
# Wiring additions to the two-LED setup:
#   - LDR + 10k divider: LDR -> 5V, 10k -> GND, junction -> A0
#
# Extra commands (case-insensitive) from phone app:
#   LDR?          -> reply once: "LDR <value>"
#   STREAM ON     -> start sending "LDR <value>" every 1s
#   STREAM OFF    -> stop streaming
#   (All LED commands from the 2-LED script are also supported.)
#
# Requirements:
#   pip install telemetrix telemetrix-lite pyserial
#   Flash Arduino with Telemetrix4Arduino.ino once.
# -----------------------------------------------------------

import time
import serial
from telemetrix_Barmaja import TelemetrixSync

# ----- SETTINGS -----
HC05_PORT = "COM8"   # <-- change to your USB-UART port for HC-05 (e.g., COM7 or /dev/ttyUSB0)
BAUD = 9600

LED1 = 8
LED2 = 9
LDR_PIN = 0         # A0

def send_line(ser, text):
    if not text.endswith("\n"):
        text += "\n"
    ser.write(text.encode())

def main():
    # 1) Arduino via telemetrix_lite
    t = TelemetrixSync()
    t.set_output(LED1); t.set_output(LED2)
    t.digital_write(LED1, 0); t.digital_write(LED2, 0)
    t.set_analog_input(LDR_PIN)

    streaming = False
    last_send = 0.0

    # 2) HC-05 serial (USB-UART)
    print(f"Opening HC-05 serial on {HC05_PORT} @ {BAUD} ...")
    with serial.Serial(HC05_PORT, BAUD, timeout=0.1) as bt:
        send_line(bt, "OK Ready: 1ON/1OFF 2ON/2OFF ALLON/ALLOFF STATE? LDR? STREAM ON/OFF")
        buf = ""
        try:
            while True:
                # A) Read commands
                ch = bt.read(1).decode(errors="ignore")
                if ch:
                    if ch in "\r\n":
                        cmd = buf.strip().upper(); buf = ""
                        if cmd:
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
                            elif cmd in ("LDR?", "LDR"):
                                v = t.analog_read(LDR_PIN, default=None)
                                if v is None: send_line(bt, "LDR None")
                                else: send_line(bt, f"LDR {v}")
                            elif cmd == "STREAM ON":
                                streaming = True; send_line(bt, "STREAM:ON")
                            elif cmd == "STREAM OFF":
                                streaming = False; send_line(bt, "STREAM:OFF")
                            else:
                                send_line(bt, f"ERR Unknown: {cmd}")
                    else:
                        buf += ch
                        if len(buf) > 64: buf = ""

                # B) Periodic stream if enabled
                now = time.time()
                if streaming and (now - last_send) >= 1.0:
                    last_send = now
                    v = t.analog_read(LDR_PIN, default=None)
                    if v is None: send_line(bt, "LDR None")
                    else: send_line(bt, f"LDR {v}")

                time.sleep(0.002)

        except KeyboardInterrupt:
            pass
        finally:
            t.shutdown()
            send_line(bt, "BYE")

if __name__ == "__main__":
    main()
