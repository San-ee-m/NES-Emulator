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
