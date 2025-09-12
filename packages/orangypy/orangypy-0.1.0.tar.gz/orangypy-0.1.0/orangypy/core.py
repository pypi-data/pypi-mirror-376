import pygame
import math

_jugando = False
_pantalla = None
_reloj = None
_sprites = []
_color_fondo = (50, 50, 50)
_fps = 60

def crear_ventana(ancho, alto, titulo, color_fondo=(50, 50, 50)):
    global _pantalla, _reloj, _color_fondo
    pygame.init()
    _pantalla = pygame.display.set_mode((ancho, alto))
    pygame.display.set_caption(titulo)
    _reloj = pygame.time.Clock()
    _color_fondo = color_fondo

def set_fps(fps):
    global _fps
    _fps = fps

def get_pantalla():
    return _pantalla

def get_dimensiones():
    return _pantalla.get_size()

def loop():
    global _jugando
    _jugando = True
    while _jugando:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _jugando = False

        from .input import chequear_teclas
        chequear_teclas()
        
        _pantalla.fill(_color_fondo)
        for s in _sprites:
            if s.get("rotacion", 0) != 0:
                img_rot = pygame.transform.rotate(s["img"], s["rotacion"])
                rect = img_rot.get_rect(center=s["img"].get_rect(topleft=(s["x"], s["y"])).center)
                _pantalla.blit(img_rot, rect.topleft)
            else:
                _pantalla.blit(s["img"], (s["x"], s["y"]))

        pygame.display.flip()
        _reloj.tick(_fps)
    pygame.quit()
