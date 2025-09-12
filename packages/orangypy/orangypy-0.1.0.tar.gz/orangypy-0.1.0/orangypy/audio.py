import pygame

_sonidos = {}
_musica_actual = None
pygame.mixer.init()

def cargar_sonido(nombre, ruta):
    _sonidos[nombre] = pygame.mixer.Sound(ruta)

def reproducir_sonido(nombre, volumen=1.0, bucle=False):
    if nombre in _sonidos:
        _sonidos[nombre].set_volume(volumen)
        _sonidos[nombre].play(-1 if bucle else 0)

def detener_sonido(nombre):
    if nombre in _sonidos:
        _sonidos[nombre].stop()

def reproducir_musica(ruta, volumen=1.0, bucle=True):
    global _musica_actual
    _musica_actual = ruta
    pygame.mixer.music.load(ruta)
    pygame.mixer.music.set_volume(volumen)
    pygame.mixer.music.play(-1 if bucle else 0)

def detener_musica():
    pygame.mixer.music.stop()

def pausar_musica():
    pygame.mixer.music.pause()

def reanudar_musica():
    pygame.mixer.music.unpause()

def set_volumen_musica(volumen):
    pygame.mixer.music.set_volume(volumen)