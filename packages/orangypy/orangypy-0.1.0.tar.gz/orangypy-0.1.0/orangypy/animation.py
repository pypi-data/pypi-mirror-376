import pygame

class Animation:
    def __init__(self, frames, duracion_frame):
        self.frames = frames
        self.duracion_frame = duracion_frame
        self.frame_actual = 0
        self.tiempo_acumulado = 0
        self.playing = False

    def play(self):
        self.playing = True
        self.frame_actual = 0
        self.tiempo_acumulado = 0

    def stop(self):
        self.playing = False
        self.frame_actual = 0

    def pause(self):
        self.playing = False

    def resume(self):
        self.playing = True

    def update(self, dt):
        if not self.playing:
            return self.frames[self.frame_actual]

        self.tiempo_acumulado += dt
        if self.tiempo_acumulado >= self.duracion_frame:
            self.tiempo_acumulado = 0
            self.frame_actual = (self.frame_actual + 1) % len(self.frames)
        
        return self.frames[self.frame_actual]

def cargar_spritesheet(ruta, ancho_frame, alto_frame):
    spritesheet = pygame.image.load(ruta)
    frames = []
    
    for y in range(0, spritesheet.get_height(), alto_frame):
        for x in range(0, spritesheet.get_width(), ancho_frame):
            frame = spritesheet.subsurface((x, y, ancho_frame, alto_frame))
            frames.append(frame)
            
    return frames

def crear_animacion(ruta_spritesheet, ancho_frame, alto_frame, duracion_frame):
    frames = cargar_spritesheet(ruta_spritesheet, ancho_frame, alto_frame)
    return Animation(frames, duracion_frame)