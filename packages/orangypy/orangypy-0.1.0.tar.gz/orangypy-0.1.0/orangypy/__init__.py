from .core import (
    crear_ventana, loop, set_fps, 
    get_pantalla, get_dimensiones
)
from .sprite import (
    dibujar, mover, rotar, obtener_sprite,
    establecer_velocidad, actualizar_sprite, colision_con
)
from .input import cuando_tecla
from .shapes import (
    circulo, rectangulo, linea,
    poligono, elipse
)
from .colors import (
    NEGRO, BLANCO, ROJO, VERDE, AZUL,
    AMARILLO, MAGENTA, CYAN, NARANJA,
    MORADO, ROSA, MARRON, GRIS, GRIS_CLARO,
    GRIS_OSCURO, VERDE_LIMA, TURQUESA,
    ORO, PLATA, INDIGO
)
from .animation import (
    crear_animacion, cargar_spritesheet
)
from .audio import (
    cargar_sonido, reproducir_sonido, detener_sonido,
    reproducir_musica, detener_musica, pausar_musica,
    reanudar_musica, set_volumen_musica
)