
import time
try:
    from telemetrix import telemetrix
except Exception as e:
    raise RuntimeError("telemetrix package is required. pip install telemetrix==1.43") from e

HIGH, LOW = 1, 0
OUTPUT, INPUT, INPUT_PULLUP = 1, 0, 2
A0, A1, A2, A3, A4, A5 = 0, 1, 2, 3, 4, 5

_ctx = None

class _Ctx:
    def __init__(self, com_port=None, **kwargs):
        # Auto-detect port if not provided
        self.board = telemetrix.Telemetrix() if com_port is None else telemetrix.Telemetrix(com_port=com_port, **kwargs)
        # Detect naming variants across telemetrix versions
        self._set_pwm   = self._detect(["set_pin_mode_pwm_output", "set_pin_mode_analog_output"])
        self._pwm_write = self._detect(["pwm_write", "analog_write"])
        self._set_dout  = self._detect(["set_pin_mode_digital_output", "set_pin_mode_output"])
        self._set_din   = self._detect(["set_pin_mode_digital_input"])
        self._set_din_pu = getattr(self.board, "set_pin_mode_digital_input_pullup", None)
        self._set_ain   = self._detect(["set_pin_mode_analog_input"])
        self._digital_read = getattr(self.board, "digital_read", None)
        self._analog_read  = getattr(self.board, "analog_read", None)
        # Optional features
        self._set_servo  = getattr(self.board, "set_pin_mode_servo", None)
        self._servo_write = getattr(self.board, "servo_write", None)
        self._set_sonar  = getattr(self.board, "set_pin_mode_sonar", None)
        self._sonar_read = getattr(self.board, "sonar_read", None)
        # State
        self._dout = set()
        self._din = {}
        self._ain = set()
        self._pwm_inited = set()
        self._servo_inited = set()
        self._sonar_inited = set()
        self._t0 = int(time.time()*1000)

    def _detect(self, names):
        for n in names:
            if hasattr(self.board, n):
                return getattr(self.board, n)
        def _missing(*args, **kwargs):
            raise RuntimeError(f"Telemetrix method missing; tried {names}")
        return _missing

    # Core API
    def pinMode(self, pin, mode):
        if mode == OUTPUT:
            self._set_dout(pin); self._dout.add(pin)
        elif mode == INPUT:
            self._set_din(pin); self._din[pin] = "in"
        elif mode == INPUT_PULLUP:
            if self._set_din_pu: self._set_din_pu(pin)
            else: self._set_din(pin)
            self._din[pin] = "in_pu"
        else:
            raise ValueError("pinMode: use OUTPUT, INPUT, or INPUT_PULLUP")

    def digitalWrite(self, pin, value):
        if pin not in self._dout:
            self._set_dout(pin); self._dout.add(pin)
        self.board.digital_write(pin, 1 if value else 0)

    def digitalRead(self, pin):
        if pin not in self._din:
            self._set_din(pin); self._din[pin] = "in"
        if not self._digital_read:
            raise RuntimeError("This Telemetrix version lacks digital_read()")
        return 1 if self._digital_read(pin) else 0

    def analogRead(self, apin):
        if apin not in self._ain:
            self._set_ain(apin); self._ain.add(apin)
        if not self._analog_read:
            raise RuntimeError("This Telemetrix version lacks analog_read()")
        v = self._analog_read(apin)
        return 0 if v is None else int(v)

    def analogWrite(self, pin, value):
        if pin not in self._pwm_inited:
            self._set_pwm(pin); self._pwm_inited.add(pin)
        self._pwm_write(pin, int(value) & 0xFF)

    def delay(self, ms): time.sleep(ms/1000.0)
    def millis(self): return int(time.time()*1000) - self._t0

    # Optional helpers
    def servoWrite(self, pin, angle):
        if self._set_servo is None or self._servo_write is None:
            raise RuntimeError("Servo not supported by this Telemetrix firmware/version.")
        if pin not in self._servo_inited:
            try:
                self._set_servo(pin)
            except TypeError:
                self._set_servo(pin, 544, 2400)
            self._servo_inited.add(pin)
        self._servo_write(pin, int(angle))

    def sonarReadCM(self, trig_pin, echo_pin):
        if self._set_sonar is None or self._sonar_read is None:
            raise RuntimeError("Sonar not supported by this Telemetrix firmware/version.")
        key = (trig_pin, echo_pin)
        if key not in self._sonar_inited:
            self._set_sonar(trig_pin, echo_pin); self._sonar_inited.add(key)
        return self._sonar_read(trig_pin, echo_pin)

    def shutdown(self):
        try:
            self.board.shutdown()
        except Exception:
            pass

# Module-level facade
def begin(com_port=None, **kwargs):
    global _ctx
    if _ctx is None:
        _ctx = _Ctx(com_port=com_port, **kwargs)
    return _ctx

def _need():
    if _ctx is None:
        raise RuntimeError("Call begin(com_port=...) first.")
    return _ctx

def pinMode(pin, mode):        _need().pinMode(pin, mode)
def digitalWrite(pin, val):    _need().digitalWrite(pin, val)
def digitalRead(pin):          return _need().digitalRead(pin)
def analogRead(apin):          return _need().analogRead(apin)
def analogWrite(pin, val):     _need().analogWrite(pin, val)
def delay(ms):                 _need().delay(ms)
def millis():                  return _need().millis()
def servoWrite(pin, angle):    _need().servoWrite(pin, angle)
def sonarReadCM(trig, echo):   return _need().sonarReadCM(trig, echo)
def shutdown():                _need().shutdown()
