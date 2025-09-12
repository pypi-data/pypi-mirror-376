import pygame
import math
from .core import _sprites

def dibujar(ruta_imagen, x, y, escala=1.0, rotacion=0):
    imagen = pygame.image.load(ruta_imagen)
    if escala != 1.0:
        nuevo_ancho = int(imagen.get_width() * escala)
        nuevo_alto = int(imagen.get_height() * escala)
        imagen = pygame.transform.scale(imagen, (nuevo_ancho, nuevo_alto))
    sprite = {
        "img": imagen,
        "x": x,
        "y": y,
        "rotacion": rotacion,
        "velocidad_x": 0,
        "velocidad_y": 0,
        "escala": escala
    }
    _sprites.append(sprite)
    return len(_sprites) - 1

def obtener_sprite(indice):
    return _sprites[indice]

def mover(indice, dx, dy):
    if isinstance(indice, int):
        _sprites[indice]["x"] += dx
        _sprites[indice]["y"] += dy
    else:
        for s in _sprites:
            s["x"] += dx
            s["y"] += dy

def rotar(indice, angulo):
    _sprites[indice]["rotacion"] = angulo

def establecer_velocidad(indice, vx, vy):
    sprite = _sprites[indice]
    sprite["velocidad_x"] = vx
    sprite["velocidad_y"] = vy

def actualizar_sprite(indice):
    sprite = _sprites[indice]
    sprite["x"] += sprite["velocidad_x"]
    sprite["y"] += sprite["velocidad_y"]

def colision_con(indice1, indice2):
    s1 = _sprites[indice1]
    s2 = _sprites[indice2]
    rect1 = s1["img"].get_rect(topleft=(s1["x"], s1["y"]))
    rect2 = s2["img"].get_rect(topleft=(s2["x"], s2["y"]))
    return rect1.colliderect(rect2)
