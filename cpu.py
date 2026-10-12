# Note: This is written with AI assistance( I do not have timme for writing the entire cpu arch )

"""
6502 CPU for the NES.

The CPU talks to the rest of the system through a "bus" object that has:
    bus.read(address)         -> byte
    bus.write(address, value)
"""

# ---- Status flag bits ----
C_FLAG = 0x01  # Carry
Z_FLAG = 0x02  # Zero
I_FLAG = 0x04  # Interrupt disable
D_FLAG = 0x08  # Decimal (stored, but ignored on the NES)
B_FLAG = 0x10  # Break (only exists on the stack copy)
U_FLAG = 0x20  # Unused (always 1)
V_FLAG = 0x40  # Overflow
N_FLAG = 0x80  # Negative

# ---- Addressing modes ----
IMP, ACC, IMM, ZP, ZPX, ZPY, ABS, ABX, ABY, IND, IZX, IZY, REL = range(13)

# ---- Opcode table: opcode -> (name, mode, cycles, extra cycle on page cross) ----
OPCODES = {}


def _ops(name, entries):
    # each entry: (mode, opcode, cycles) or (mode, opcode, cycles, True)
    # the optional True means "+1 cycle if a page boundary is crossed"
    for entry in entries:
        mode, opcode, cycles = entry[0], entry[1], entry[2]
        penalty = len(entry) > 3
        OPCODES[opcode] = (name, mode, cycles, penalty)


def _alu(name, base):
    # These 7 instructions all follow the same opcode pattern.
    _ops(name, [
        (IMM, base + 0x09, 2),
        (ZP,  base + 0x05, 3),
        (ZPX, base + 0x15, 4),
        (ABS, base + 0x0D, 4),
        (ABX, base + 0x1D, 4, True),
        (ABY, base + 0x19, 4, True),
        (IZX, base + 0x01, 6),
        (IZY, base + 0x11, 5, True),
    ])


for _name, _base in (("ORA", 0x00), ("AND", 0x20), ("EOR", 0x40), ("ADC", 0x60),
                     ("LDA", 0xA0), ("CMP", 0xC0), ("SBC", 0xE0)):
    _alu(_name, _base)

# STA is like the group above, but it has no immediate mode and no page penalty
_ops("STA", [(ZP, 0x85, 3), (ZPX, 0x95, 4), (ABS, 0x8D, 4),
             (ABX, 0x9D, 5), (ABY, 0x99, 5), (IZX, 0x81, 6), (IZY, 0x91, 6)])

# Shifts and rotates
_ops("ASL", [(ACC, 0x0A, 2), (ZP, 0x06, 5), (ZPX, 0x16, 6), (ABS, 0x0E, 6), (ABX, 0x1E, 7)])
_ops("LSR", [(ACC, 0x4A, 2), (ZP, 0x46, 5), (ZPX, 0x56, 6), (ABS, 0x4E, 6), (ABX, 0x5E, 7)])
_ops("ROL", [(ACC, 0x2A, 2), (ZP, 0x26, 5), (ZPX, 0x36, 6), (ABS, 0x2E, 6), (ABX, 0x3E, 7)])
_ops("ROR", [(ACC, 0x6A, 2), (ZP, 0x66, 5), (ZPX, 0x76, 6), (ABS, 0x6E, 6), (ABX, 0x7E, 7)])

# Increment / decrement memory
_ops("INC", [(ZP, 0xE6, 5), (ZPX, 0xF6, 6), (ABS, 0xEE, 6), (ABX, 0xFE, 7)])
_ops("DEC", [(ZP, 0xC6, 5), (ZPX, 0xD6, 6), (ABS, 0xCE, 6), (ABX, 0xDE, 7)])

# Load / store X and Y
_ops("LDX", [(IMM, 0xA2, 2), (ZP, 0xA6, 3), (ZPY, 0xB6, 4), (ABS, 0xAE, 4), (ABY, 0xBE, 4, True)])
_ops("LDY", [(IMM, 0xA0, 2), (ZP, 0xA4, 3), (ZPX, 0xB4, 4), (ABS, 0xAC, 4), (ABX, 0xBC, 4, True)])
_ops("STX", [(ZP, 0x86, 3), (ZPY, 0x96, 4), (ABS, 0x8E, 4)])
_ops("STY", [(ZP, 0x84, 3), (ZPX, 0x94, 4), (ABS, 0x8C, 4)])

# Compare X / Y, and BIT
_ops("CPX", [(IMM, 0xE0, 2), (ZP, 0xE4, 3), (ABS, 0xEC, 4)])
_ops("CPY", [(IMM, 0xC0, 2), (ZP, 0xC4, 3), (ABS, 0xCC, 4)])
_ops("BIT", [(ZP, 0x24, 3), (ABS, 0x2C, 4)])

# Jumps and calls
_ops("JMP", [(ABS, 0x4C, 3), (IND, 0x6C, 5)])
_ops("JSR", [(ABS, 0x20, 6)])
_ops("RTS", [(IMP, 0x60, 6)])
_ops("RTI", [(IMP, 0x40, 6)])
_ops("BRK", [(IMP, 0x00, 7)])

# Branches (2 cycles, +1 if taken, +1 more if it crosses a page)
_ops("BPL", [(REL, 0x10, 2)])
_ops("BMI", [(REL, 0x30, 2)])
_ops("BVC", [(REL, 0x50, 2)])
_ops("BVS", [(REL, 0x70, 2)])
_ops("BCC", [(REL, 0x90, 2)])
_ops("BCS", [(REL, 0xB0, 2)])
_ops("BNE", [(REL, 0xD0, 2)])
_ops("BEQ", [(REL, 0xF0, 2)])

# One-byte instructions
for _name, _opcode in (("CLC", 0x18), ("SEC", 0x38), ("CLI", 0x58), ("SEI", 0x78),
                       ("CLV", 0xB8), ("CLD", 0xD8), ("SED", 0xF8), ("NOP", 0xEA),
                       ("TAX", 0xAA), ("TXA", 0x8A), ("TAY", 0xA8), ("TYA", 0x98),
                       ("TSX", 0xBA), ("TXS", 0x9A), ("DEX", 0xCA), ("DEY", 0x88),
                       ("INX", 0xE8), ("INY", 0xC8)):
    _ops(_name, [(IMP, _opcode, 2)])

# Stack
_ops("PHA", [(IMP, 0x48, 3)])
_ops("PHP", [(IMP, 0x08, 3)])
_ops("PLA", [(IMP, 0x68, 4)])
_ops("PLP", [(IMP, 0x28, 4)])


class CPU6502:
    def __init__(self, bus):
        self.bus = bus

        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFD
        self.pc = 0
        self.status = 0x24  # I flag and U flag set
        self.cycles = 0     # total cycles run so far

        # Link every opcode to its handler method (op_LDA, op_STA, ...).
        # If a handler is missing, this line raises an error right away.
        self.table = {}
        for opcode, (name, mode, cycles, penalty) in OPCODES.items():
            self.table[opcode] = (getattr(self, "op_" + name), mode, cycles, penalty)

    # ------------------------------------------------------------------
    # Memory and flag helpers
    # ------------------------------------------------------------------
    def read(self, address):
        return self.bus.read(address & 0xFFFF)

    def write(self, address, value):
        self.bus.write(address & 0xFFFF, value & 0xFF)

    def _read16(self, address):
        lo = self.read(address)
        hi = self.read(address + 1)
        return lo | (hi << 8)

    def _fetch(self):
        """Read the byte at PC, then move PC forward by 1."""
        value = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return value

    def _fetch16(self):
        lo = self._fetch()
        hi = self._fetch()
        return lo | (hi << 8)

    def _flag(self, mask):
        return bool(self.status & mask)

    def _set_flag(self, mask, condition):
        if condition:
            self.status |= mask
        else:
            self.status &= ~mask & 0xFF

    def _set_zn(self, value):
        self._set_flag(Z_FLAG, value == 0)
        self._set_flag(N_FLAG, value & 0x80)
        return value

    def _push(self, value):
        self.write(0x0100 + self.sp, value)
        self.sp = (self.sp - 1) & 0xFF

    def _pull(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read(0x0100 + self.sp)

    # ------------------------------------------------------------------
    # Reset and interrupts
    # ------------------------------------------------------------------
    def reset(self):
        self.a = 0
        self.x = 0
        self.y = 0
        self.sp = 0xFD
        self.status = 0x24
        self.pc = self._read16(0xFFFC)
        self.cycles = 7

    def _interrupt(self, vector, is_brk):
        self._push(self.pc >> 8)
        self._push(self.pc & 0xFF)
        pushed = (self.status | U_FLAG) & ~B_FLAG & 0xFF
        if is_brk:
            pushed |= B_FLAG
        self._push(pushed)
        self._set_flag(I_FLAG, True)
        self.pc = self._read16(vector)

    def nmi(self):
        """Non-maskable interrupt. The PPU will call this at the start of vblank."""
        self._interrupt(0xFFFA, False)
        self.cycles += 7
        return 7

    def irq(self):
        """Normal interrupt. Ignored when the I flag is set."""
        if self._flag(I_FLAG):
            return 0
        self._interrupt(0xFFFE, False)
        self.cycles += 7
        return 7

    # ------------------------------------------------------------------
    # Run one instruction
    # ------------------------------------------------------------------
    def step(self):
        """Run one instruction. Returns how many cycles it took."""
        opcode_address = self.pc
        opcode = self._fetch()

        entry = self.table.get(opcode)
        if entry is None:
            raise ValueError(f"Unknown opcode {opcode:02X} at address {opcode_address:04X}")

        handler, mode, cycles, penalty = entry

        address, page_crossed = self._get_address(mode)
        if penalty and page_crossed:
            cycles += 1

        extra = handler(address)  # branches return extra cycles
        if extra:
            cycles += extra

        self.cycles += cycles
        return cycles

    def _get_address(self, mode):
        """Work out the address the instruction uses.
        Returns (address, page_crossed). Address is None for IMP and ACC."""
        if mode == IMP or mode == ACC:
            return None, False

        if mode == IMM:
            address = self.pc
            self.pc = (self.pc + 1) & 0xFFFF
            return address, False

        if mode == ZP:
            return self._fetch(), False

        if mode == ZPX:
            return (self._fetch() + self.x) & 0xFF, False

        if mode == ZPY:
            return (self._fetch() + self.y) & 0xFF, False

        if mode == ABS:
            return self._fetch16(), False

        if mode == ABX:
            base = self._fetch16()
            address = (base + self.x) & 0xFFFF
            return address, (base & 0xFF00) != (address & 0xFF00)

        if mode == ABY:
            base = self._fetch16()
            address = (base + self.y) & 0xFFFF
            return address, (base & 0xFF00) != (address & 0xFF00)

        if mode == IND:
            # Real 6502 bug: if the pointer is at $xxFF, the high byte
            # is read from $xx00, not from the next page.
            pointer = self._fetch16()
            lo = self.read(pointer)
            hi = self.read((pointer & 0xFF00) | ((pointer + 1) & 0x00FF))
            return lo | (hi << 8), False

        if mode == IZX:
            zp = (self._fetch() + self.x) & 0xFF
            lo = self.read(zp)
            hi = self.read((zp + 1) & 0xFF)
            return lo | (hi << 8), False

        if mode == IZY:
            zp = self._fetch()
            lo = self.read(zp)
            hi = self.read((zp + 1) & 0xFF)
            base = lo | (hi << 8)
            address = (base + self.y) & 0xFFFF
            return address, (base & 0xFF00) != (address & 0xFF00)

        if mode == REL:
            offset = self._fetch()
            if offset & 0x80:
                offset -= 0x100  # make it a signed number
            return (self.pc + offset) & 0xFFFF, False

        raise ValueError(f"Unknown addressing mode {mode}")

    # ------------------------------------------------------------------
    # Instructions: load / store / transfer
    # ------------------------------------------------------------------
    def op_LDA(self, addr): self.a = self._set_zn(self.read(addr))
    def op_LDX(self, addr): self.x = self._set_zn(self.read(addr))
    def op_LDY(self, addr): self.y = self._set_zn(self.read(addr))

    def op_STA(self, addr): self.write(addr, self.a)
    def op_STX(self, addr): self.write(addr, self.x)
    def op_STY(self, addr): self.write(addr, self.y)

    def op_TAX(self, addr): self.x = self._set_zn(self.a)
    def op_TAY(self, addr): self.y = self._set_zn(self.a)
    def op_TXA(self, addr): self.a = self._set_zn(self.x)
    def op_TYA(self, addr): self.a = self._set_zn(self.y)
    def op_TSX(self, addr): self.x = self._set_zn(self.sp)
    def op_TXS(self, addr): self.sp = self.x  # no flags change

    # ------------------------------------------------------------------
    # Instructions: stack
    # ------------------------------------------------------------------
    def op_PHA(self, addr): self._push(self.a)
    def op_PHP(self, addr): self._push(self.status | B_FLAG | U_FLAG)
    def op_PLA(self, addr): self.a = self._set_zn(self._pull())
    def op_PLP(self, addr): self.status = (self._pull() & ~B_FLAG & 0xFF) | U_FLAG

    # ------------------------------------------------------------------
    # Instructions: logic and math
    # ------------------------------------------------------------------
    def op_AND(self, addr): self.a = self._set_zn(self.a & self.read(addr))
    def op_ORA(self, addr): self.a = self._set_zn(self.a | self.read(addr))
    def op_EOR(self, addr): self.a = self._set_zn(self.a ^ self.read(addr))

    def _add_with_carry(self, value):
        total = self.a + value + (1 if self._flag(C_FLAG) else 0)
        result = total & 0xFF
        self._set_flag(C_FLAG, total > 0xFF)
        # Overflow: both inputs have the same sign, the result has a different sign
        self._set_flag(V_FLAG, ~(self.a ^ value) & (self.a ^ result) & 0x80)
        self.a = self._set_zn(result)

    def op_ADC(self, addr): self._add_with_carry(self.read(addr))
    def op_SBC(self, addr): self._add_with_carry(self.read(addr) ^ 0xFF)  # A - M = A + ~M + C

    def _compare(self, register, value):
        self._set_flag(C_FLAG, register >= value)
        self._set_zn((register - value) & 0xFF)

    def op_CMP(self, addr): self._compare(self.a, self.read(addr))
    def op_CPX(self, addr): self._compare(self.x, self.read(addr))
    def op_CPY(self, addr): self._compare(self.y, self.read(addr))

    def op_BIT(self, addr):
        value = self.read(addr)
        self._set_flag(Z_FLAG, (self.a & value) == 0)
        self._set_flag(V_FLAG, value & 0x40)
        self._set_flag(N_FLAG, value & 0x80)

    def op_INX(self, addr): self.x = self._set_zn((self.x + 1) & 0xFF)
    def op_INY(self, addr): self.y = self._set_zn((self.y + 1) & 0xFF)
    def op_DEX(self, addr): self.x = self._set_zn((self.x - 1) & 0xFF)
    def op_DEY(self, addr): self.y = self._set_zn((self.y - 1) & 0xFF)

    def op_INC(self, addr): self.write(addr, self._set_zn((self.read(addr) + 1) & 0xFF))
    def op_DEC(self, addr): self.write(addr, self._set_zn((self.read(addr) - 1) & 0xFF))

    # ------------------------------------------------------------------
    # Instructions: shifts and rotates
    # (addr is None means "use the A register")
    # ------------------------------------------------------------------
    def _shift(self, addr, operation):
        value = self.a if addr is None else self.read(addr)
        result = operation(value) & 0xFF
        self._set_zn(result)
        if addr is None:
            self.a = result
        else:
            self.write(addr, result)

    def op_ASL(self, addr):
        def operation(v):
            self._set_flag(C_FLAG, v & 0x80)
            return v << 1
        self._shift(addr, operation)

    def op_LSR(self, addr):
        def operation(v):
            self._set_flag(C_FLAG, v & 0x01)
            return v >> 1
        self._shift(addr, operation)

    def op_ROL(self, addr):
        def operation(v):
            old_carry = 1 if self._flag(C_FLAG) else 0
            self._set_flag(C_FLAG, v & 0x80)
            return (v << 1) | old_carry
        self._shift(addr, operation)

    def op_ROR(self, addr):
        def operation(v):
            old_carry = 0x80 if self._flag(C_FLAG) else 0
            self._set_flag(C_FLAG, v & 0x01)
            return (v >> 1) | old_carry
        self._shift(addr, operation)

    # ------------------------------------------------------------------
    # Instructions: flags
    # ------------------------------------------------------------------
    def op_CLC(self, addr): self._set_flag(C_FLAG, False)
    def op_SEC(self, addr): self._set_flag(C_FLAG, True)
    def op_CLI(self, addr): self._set_flag(I_FLAG, False)
    def op_SEI(self, addr): self._set_flag(I_FLAG, True)
    def op_CLV(self, addr): self._set_flag(V_FLAG, False)
    def op_CLD(self, addr): self._set_flag(D_FLAG, False)
    def op_SED(self, addr): self._set_flag(D_FLAG, True)
    def op_NOP(self, addr): pass

    # ------------------------------------------------------------------
    # Instructions: jumps, calls, branches
    # ------------------------------------------------------------------
    def op_JMP(self, addr): self.pc = addr

    def op_JSR(self, addr):
        return_address = (self.pc - 1) & 0xFFFF  # last byte of the JSR instruction
        self._push(return_address >> 8)
        self._push(return_address & 0xFF)
        self.pc = addr

    def op_RTS(self, addr):
        lo = self._pull()
        hi = self._pull()
        self.pc = (((hi << 8) | lo) + 1) & 0xFFFF

    def op_RTI(self, addr):
        self.status = (self._pull() & ~B_FLAG & 0xFF) | U_FLAG
        lo = self._pull()
        hi = self._pull()
        self.pc = (hi << 8) | lo

    def op_BRK(self, addr):
        self.pc = (self.pc + 1) & 0xFFFF  # BRK skips one padding byte
        self._interrupt(0xFFFE, True)

    def _branch(self, condition, target):
        """Returns the extra cycles: 0 not taken, 1 taken, 2 taken + page cross."""
        if not condition:
            return 0
        extra = 2 if (self.pc & 0xFF00) != (target & 0xFF00) else 1
        self.pc = target
        return extra

    def op_BPL(self, addr): return self._branch(not self._flag(N_FLAG), addr)
    def op_BMI(self, addr): return self._branch(self._flag(N_FLAG), addr)
    def op_BVC(self, addr): return self._branch(not self._flag(V_FLAG), addr)
    def op_BVS(self, addr): return self._branch(self._flag(V_FLAG), addr)
    def op_BCC(self, addr): return self._branch(not self._flag(C_FLAG), addr)
    def op_BCS(self, addr): return self._branch(self._flag(C_FLAG), addr)
    def op_BNE(self, addr): return self._branch(not self._flag(Z_FLAG), addr)
    def op_BEQ(self, addr): return self._branch(self._flag(Z_FLAG), addr)


