import serial, time
class PN532HSU:
    PREAMBLE=b"\x00\x00\xFF"; HOST_TFI=0xD4; DEV_TFI=0xD5
    def __init__(self,port,baud=115200,timeout=0.5): self.ser=serial.Serial(port,baud,timeout=timeout); time.sleep(0.1)
    def _frame(self,cmd): tfi=bytes([self.HOST_TFI]); payload=tfi+cmd; ln=len(payload)&0xFF; lcs=((~ln+1)&0xFF); dcs=((~(sum(payload)&0xFF)+1)&0xFF); return self.PREAMBLE+bytes([ln,lcs])+payload+bytes([dcs,0x00])
    def _write_cmd(self,cmd): self.ser.write(self._frame(cmd))
    def _read_payload(self):
        h=self.ser.read(3); 
        if h!=self.PREAMBLE: return None
        ln=self.ser.read(1); 
        if not ln: return None
        ln=ln[0]; self.ser.read(1); payload=self.ser.read(ln); dcs=self.ser.read(1); post=self.ser.read(1)
        if len(payload)!=ln or len(dcs)!=1 or post!=b"\x00": return None
        return payload
    def sam_configuration(self): self._write_cmd(b"\x14\x01\x14\x01"); return self._read_payload()
    def in_list_passive_target_106A(self): self._write_cmd(b"\x4A\x01\x00"); return self._read_payload()
    def read_uid(self,tries=20,delay=0.2):
        self.sam_configuration()
        for _ in range(tries):
            resp=self.in_list_passive_target_106A()
            if not resp: time.sleep(delay); continue
            if len(resp)>=3 and resp[0]==self.DEV_TFI and resp[1]==0x4B:
                for off in (6,7,8):
                    if off<len(resp):
                        l=resp[off]; end=off+1+l
                        if l in (4,7,10) and end<=len(resp): uid=resp[off+1:end]; return ''.join(f'{b:02X}' for b in uid)
            time.sleep(delay)
        return None
