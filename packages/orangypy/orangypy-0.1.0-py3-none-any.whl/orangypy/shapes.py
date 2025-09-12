import pygame
from .core import get_pantalla

def rectangulo(x, y, ancho, alto, color, relleno=True, grosor=1):
    if relleno:
        pygame.draw.rect(get_pantalla(), color, (x, y, ancho, alto))
    else:
        pygame.draw.rect(get_pantalla(), color, (x, y, ancho, alto), grosor)

def circulo(x, y, radio, color, relleno=True, grosor=1):
    if relleno:
        pygame.draw.circle(get_pantalla(), color, (x, y), radio)
    else:
        pygame.draw.circle(get_pantalla(), color, (x, y), radio, grosor)

def linea(x1, y1, x2, y2, color, grosor=1):
    pygame.draw.line(get_pantalla(), color, (x1, y1), (x2, y2), grosor)

def poligono(puntos, color, relleno=True, grosor=1):
    if relleno:
        pygame.draw.polygon(get_pantalla(), color, puntos)
    else:
        pygame.draw.polygon(get_pantalla(), color, puntos, grosor)

def elipse(x, y, ancho, alto, color, relleno=True, grosor=1):
    if relleno:
        pygame.draw.ellipse(get_pantalla(), color, (x, y, ancho, alto))
    else:
        pygame.draw.ellipse(get_pantalla(), color, (x, y, ancho, alto), grosor)