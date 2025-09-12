import pygame

_teclas = {}

def cuando_tecla(tecla, funcion):
    _teclas[tecla] = funcion

def chequear_teclas():
    keys = pygame.key.get_pressed()
    for k, f in _teclas.items():
        if keys[getattr(pygame, f"K_{k}")]:
            f()
