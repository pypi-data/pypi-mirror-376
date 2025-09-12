# rfid_rc522_serial_reader.py
# -----------------------------------------------------------
# RC522 RFID (SPI) -> Arduino bridge -> Python
#
# Why a bridge?
#   - RC522 talks SPI; Telemetrix does not expose MFRC522 commands.
#   - Easiest classroom flow: a tiny Arduino sketch prints the UID
#     to Serial. Python just reads the UID from COM and uses it.
#
# What you need
#   1) Hardware:
#       - Arduino UNO
#       - RC522 module (MFRC522)
#       - Jumper wires
#   2) Arduino libraries:
#       - MFRC522 by Miguel Balboa (install from Arduino Library Manager)
#   3) Sketch to upload to Arduino:
#       - Use the standard UID printer (example below).
#         This prints one line per card: e.g. 'A1B2C3D4'
#
#      ------------------ rc522_uid.ino ------------------
#      #include <SPI.h>
#      #include <MFRC522.h>
#      #define SS_PIN 10
#      #define RST_PIN 9
#      MFRC522 rfid(SS_PIN, RST_PIN);
#      void setup(){
#        Serial.begin(9600);
#        SPI.begin();
#        rfid.PCD_Init();
#        Serial.println("RC522 UID ready");
#      }
#      void loop(){
#        if (!rfid.PICC_IsNewCardPresent()) return;
#        if (!rfid.PICC_ReadCardSerial()) return;
#        for (byte i = 0; i < rfid.uid.size; i++){
#          if (rfid.uid.uidByte[i] < 0x10) Serial.print("0");
#          Serial.print(rfid.uid.uidByte[i], HEX);
#        }
#        Serial.println();
#        rfid.PICC_HaltA();
#        delay(500);
#      }
#      ----------------------------------------------------
#
# Wiring RC522 -> Arduino UNO (SPI):
#   RC522 SDA(SS) -> D10
#   RC522 SCK     -> D13
#   RC522 MOSI    -> D11
#   RC522 MISO    -> D12
#   RC522 RST     -> D9
#   RC522 3.3V    -> 3.3V   (IMPORTANT: RC522 is 3.3V)
#   RC522 GND     -> GND
#
# Steps
#   1) Upload the sketch above to the Arduino (close Serial Monitor after).
#   2) Note the Arduino COM port (e.g., COM5 / /dev/ttyACM0).
#   3) Run this Python script; it reads UID lines and prints them.
#   4) Integrate with your app (e.g., compare UID to a whitelist).
#
# Teacher tips
#   - Have at least 2 different tags/cards to demo different UIDs.
#   - If you see gibberish, check you’re at 9600 baud and Serial Monitor is closed.
#   - For access projects, combine with a servo or LED logic in a second script.
#
# -----------------------------------------------------------

import time
import serial

PORT = "COM5"   # <-- change to your Arduino port
BAUD = 9600

def main():
    print(f"Opening serial {PORT} @ {BAUD} ... Tap cards to the RC522.")
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        try:
            while True:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    uid = line.upper()
                    print("UID:", uid)
                    # TODO: replace with your logic, e.g.:
                    # if uid in {"DEADBEEF", "A1B2C3D4"}: print("Access GRANTED")
                    # else: print("Access DENIED")
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\nStopped.")

if __name__ == "__main__":
    main()
