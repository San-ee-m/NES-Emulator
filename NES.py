import pygame

class Cartridge:
    def __init__(self, file_path):
        self.file_path = file_path

        # program ROM and character ROM
        self.prg_rom = bytearray()
        self.chr_rom = bytearray()

        self.prg_rom_size = 0
        self.chr_rom_size = 0

        self.mapper = 0
        self.mirroring = "VERTICAL"
        self.has_battery = False
        self.has_trainer = False

        #UROM state
        self.selected_bank = 0

        self._load_nes_file()

    def _load_nes_file(self):
        with open(self.file_path, "rb") as f:
            header = f.read(16)
            if header[0:4] != b"NES\x1a":
                raise ValueError("Not a valid NES file")

            self.prg_rom_size = header[4] 
            self.chr_rom_size = header[5]

            flag_vert = header[6] 
            flag_horiz = header[7]

            self.mapper = (flag_vert >> 4) | (flag_horiz & 0xF0)

            self.mirroring = "VERTICAL" if (flag_vert & 0x01) else "HORIZONTAL"
            self.has_battery = bool(flag_vert & 0x02)
            self.has_trainer = bool(flag_vert & 0x04)

            if self.has_trainer:
                f.read(512)  # Skip trainer data

            # Read PRG ROM data
            prg_size = self.prg_rom_size * 16384  # Each PRG ROM bank is 16KB
            self.prg_rom = bytearray(f.read(prg_size))  

            # Read CHR ROM data
            chr_size = self.chr_rom_size * 8192  # Each CHR ROM bank is 8KB
            if chr_size > 0:
                self.chr_rom = bytearray(f.read(chr_size))  # load file
            else:
                self.chr_rom = bytearray(8192)  # Allocate 8KB of CHR RAM if no CHR ROM is present

            self.num_prg_banks = self.prg_rom_size # Default for UROM


    def cpu_read(self, address):
        if 0x8000 <= address <= 0xBFFF:
            bank_offset = self.selected_bank * 16384
            offset_bank = address - 0x8000
            return self.prg_rom[bank_offset + offset_bank]
        
        elif 0x8000 <= address <= 0xFFFF:
            last_bank = self.num_prg_banks - 1
            bank_offset = last_bank * 16384
            offset_bank = address - 0xC000
            return self.prg_rom[bank_offset + offset_bank]
        
        return 0

    def cpu_write(self, address,value):
        if 0x8000 <= address <= 0xFFFF:
            self.selected_bank = value & (self.prg_rom_size - 1)  # for Mapper 2

    def ppu_read(self, address):
        if 0x0000 <= address <= 0x1FFF:
            return self.chr_rom[address]
        return 0

    def ppu_write(self, address, value):
        if 0x0000 <= address <= 0x1FFF:
            self.chr_rom[address] = value & 0xFF
            

        

NES_WIDTH = 256
NES_HEIGHT = 240

Scale = 3

width = NES_WIDTH * Scale
height = NES_HEIGHT * Scale

pygame.init()

screen = pygame.display.set_mode((width, height))

canvas  = pygame.Surface((NES_WIDTH, NES_HEIGHT))

pygame.display.set_caption("EMULATOR 3000")

clock = pygame.time.Clock()

running = True  
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    #CPU here  and PPU here

    #Clear the canvas
    canvas.fill((0, 0, 0))  
    pygame.draw.rect(canvas,(255, 0, 0), (50, 50, 100, 100))  

    #Scaling
    scaled_screen = pygame.transform.scale(canvas,(width,height))
    screen.blit(scaled_screen,(0,0))
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(60)

pygame.quit()
