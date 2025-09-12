from telemetrix_Barmaja.rfid_pn532 import PN532HSU

pn = PN532HSU(port='COM8', baud=115200)
print('SAM config:', pn.sam_configuration())
print('Tap a card...')
while True:
    uid = pn.read_uid()
    if uid:
        print('UID:', uid)
