

class SoftCodeHandler(self):
    def __init__(self):
        import importlib
        self.pg = importlib.import_module('pygame')
        from pygame.locals import *
        self.pg.init()
        screen = pygame.display.set_mode((1920, 1080), pygame.NOFRAME)
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((250, 250, 250))


        charRect = pygame.Rect((0,0),(1920, 1080))
        gratingIm = pygame.image.load("/home/pi/Mouse_Academy/Python_RasPi/Software/GratingLick/gratingIms/grating_rot=-30degrees_period=05_size=15_xoffset=+000_yoffset=+000.jpg")
        gratingIm = pygame.transform.scale(gratingIm, charRect.size)
        gratingIm = gratingIm.convert()

        background.blit(gratingIm, charRect) #This just makes it in the same location
                                     #and prints it the same size as the image


        screen.blit(background,(0,0))
    def handleSoftCode(byte):
        if byte==1:
        elif byte==2:
