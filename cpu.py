"""
6502 CPU for the NES.

"""

# Status flags (each flag is one bit)

c_flag = 0x001 # this is the carry flag
z_flag = 0x002 # this is the zero flag
i_flag = 0x004 # this is the interrupt flag
d_flag = 0x008 # this is the decimal flag
b_flag = 0x010 # this is the break flag
u_flag = 0x020 # this is the flag for unused
o_flag = 0x040 # this is the overflow flag
n_flag = 0x080 # this is the negative flag




class CPU6502:
    def __init__(self, bus):
        self.bus = bus
        self.a = 0  # - > main register
        self.x = 0 
        self.y = 0 # -> x,y are helper registers
        self.sp = 0xFD # -> Stack pointer
        self.pc = 0 # -> program counter
        self.status = 0x24 # -> 8 flags in one byte
        self.cycle = 0 # Counter for cpu cycles

    def read(self,address):
        return self.bus.read(address & 0xFFFF)

    def write(self,address,value):
        self.bus.write(address & 0xFFFF,value & 0xFF)

    def reset(self):
        # repeated because this state can be called multiple times
        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFD
        self.status = 0x24

        # reset vector
        lo = self.read(0xFFFC)
        hi = self.read(0xFFFD)

        #joining to 16bits to form address
        self.pc = lo | (hi << 8)

        # setting cycle to 7
        self.cycle = 7

    def flag(self,mask):
        # returns wether flag is on or off
        return bool(self.status & mask)

    def set_flag(self,mask,condition):
        if condition:
            self.status |= mask
        else:
            self.status &= ~mask & 0xFF

    def zn_flag(self,value):
        self.set_flag(z_flag,value == 0)
        self.set_flag(n_flag,value & 0x80)
        return value


class FakeBus:
    def read(self,a):
        return 0
    def write(self,a,v):
        pass


cpu = CPU6502(FakeBus)

cpu.set_flag(c_flag,True)
print(bin(cpu.status))

cpu.zn_flag(0)
print(bin(cpu.status))

cpu.zn_flag(0X80)
print(bin(cpu.status))

cpu.set_flag(c_flag,False)
print(bin(cpu.status))
