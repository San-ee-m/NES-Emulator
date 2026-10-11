import pygame

NES_WIDTH = 256
NES_HEIGHT = 240

Scale = 3

width = NES_WIDTH * Scale
height = NES_HEIGHT * Scale

pygame.init()

screen = pygame.display.set_mode((width, height))

canvas  = pygame.Surface((NES_WIDTH, NES_HEIGHT))

pygame.display_set_caption("EMULATOR 3000")

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
    pygame.transform.scale(canvas,(width,height),screen)
    pygame.display.flip()
    
    # Cap the frame rate
    clock.tick(60)

pygame.quit()
