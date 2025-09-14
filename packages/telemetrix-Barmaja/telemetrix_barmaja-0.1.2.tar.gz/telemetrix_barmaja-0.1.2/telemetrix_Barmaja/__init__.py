
from . import telemetrixsync
from .telemetrixsync import HIGH, LOW, OUTPUT, INPUT, INPUT_PULLUP, A0, A1, A2, A3, A4, A5
from ._version import __version__

class TelemetrixSync:
    """Class adapter over telemetrixsync's Arduino-like API."""
    def __init__(self, com_port=None, **kwargs):
        telemetrixsync.begin(com_port=com_port, **kwargs)
    def pinMode(self, pin, mode):        telemetrixsync.pinMode(pin, mode)
    def digitalWrite(self, pin, val):    telemetrixsync.digitalWrite(pin, val)
    def digitalRead(self, pin):          return telemetrixsync.digitalRead(pin)
    def analogRead(self, apin):          return telemetrixsync.analogRead(apin)
    def analogWrite(self, pin, val):     telemetrixsync.analogWrite(pin, val)
    def delay(self, ms):                 telemetrixsync.delay(ms)
    def millis(self):                    return telemetrixsync.millis()
    def servoWrite(self, pin, angle):    telemetrixsync.servoWrite(pin, angle)
    def sonarReadCM(self, trig, echo):   return telemetrixsync.sonarReadCM(trig, echo)
    def shutdown(self):                  telemetrixsync.shutdown()

# helper to get examples path from installed package
import os as _os, importlib.resources as _res
def examples_path() -> str:
    try:
        with _res.as_file(_res.files(__package__) / "examples") as p:
            return str(p)
    except Exception:
        return _os.path.join(_os.path.dirname(__file__), "examples")
