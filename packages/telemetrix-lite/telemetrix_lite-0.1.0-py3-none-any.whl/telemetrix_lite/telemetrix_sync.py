import time
from telemetrix import telemetrix
class TelemetrixSync:
    def __init__(self, com_port=None, enable_prints=False):
        self.board = telemetrix.Telemetrix() if com_port is None else telemetrix.Telemetrix(com_port=com_port)
        self._d_cache={}; self._a_cache={}; self._last_change={}; self._prints=enable_prints
    def _digital_cb(self,data):
        pin=data[1]; val=1 if data[2] else 0; self._d_cache[pin]=val; self._last_change[pin]=time.time()
        if self._prints: print(f"[DIGITAL {pin}]={val}")
    def _analog_cb(self,data):
        pin=data[1]; val=int(data[2]); self._a_cache[pin]=val; self._last_change[pin]=time.time()
        if self._prints: print(f"[ANALOG A{pin}]={val}")
    def set_input(self,pin,pullup=False):
        (self.board.set_pin_mode_digital_input_pullup if pullup else self.board.set_pin_mode_digital_input)(pin,callback=self._digital_cb)
    def set_output(self,pin): self.board.set_pin_mode_digital_output(pin)
    def set_analog_input(self,a_pin): self.board.set_pin_mode_analog_input(a_pin,callback=self._analog_cb)
    def digital_read(self,pin,default=None): return self._d_cache.get(pin,default)
    def analog_read(self,a_pin,default=None): return self._a_cache.get(a_pin,default)
    def digital_read_debounced(self,pin,stable_ms=30,default=None):
        v=self._d_cache.get(pin); t=self._last_change.get(pin); 
        if v is None or t is None: return default
        return v if (time.time()-t)*1000.0>=stable_ms else default
    def digital_write(self,pin,value): self.board.digital_write(pin,1 if value else 0)
    def pwm_write(self,pin,val): self.board.set_pin_mode_pwm_output(pin); self.board.pwm_write(pin,int(val))
    def servo_write(self,pin,ang): self.board.set_pin_mode_servo(pin); self.board.servo_write(pin,int(ang))
    def sonar_config(self,trig,echo): self.board.set_pin_mode_sonar(trig,echo)
    def sonar_read(self,trig): return self.board.sonar_read(trig)
    def i2c_init(self,addr=0x27):
        self._i2c_addr=addr; self.board.i2c_config(); self._LCD_EN=0x04; self._LCD_RS=0x01; self._LCD_BL=0x08
        time.sleep(0.05); 
        for cmd in (0x33,0x32,0x28,0x0C,0x06,0x01):
            self._lcd_cmd(cmd); time.sleep(0.005)
    def _i2c_write(self,data): self.board.i2c_write(self._i2c_addr,[data])
    def _lcd_pulse(self,data): self._i2c_write(data|self._LCD_EN); time.sleep(0.001); self._i2c_write(data & ~self._LCD_EN)
    def _lcd_write4(self,bits,rs): data=(bits & 0xF0)|self._LCD_BL|(self._LCD_RS if rs else 0); self._lcd_pulse(data)
    def _lcd_cmd(self,cmd): self._lcd_write4(cmd,0); self._lcd_write4(cmd<<4,0)
    def _lcd_data(self,val): self._lcd_write4(val,1); self._lcd_write4(val<<4,1)
    def lcd_print(self,row,col,text):
        if not hasattr(self,'_i2c_addr'): raise RuntimeError('Call i2c_init(addr) first')
        addr=0x80+(0x40*row)+col; self._lcd_cmd(addr)
        for ch in text[:16-col]: self._lcd_data(ord(ch))
    def shutdown(self):
        try: self.board.shutdown()
        except Exception as e:
            if self._prints: print('[TelemetrixSync] shutdown warning:',e)
