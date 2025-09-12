# OrangyPy - Motor de Juegos 2D Simple y Poderoso 🎮

OrangyPy es una biblioteca de Python diseñada para crear juegos 2D de forma fácil y rápida, perfecta para principiantes y educadores.

## 🚀 Instalación

```bash
pip install orangypy
```

## 🎯 Características Principales

- 🖼️ Sistema de sprites y animaciones
- 🎵 Sistema de audio (efectos de sonido y música)
- ⌨️ Control de entrada simplificado
- 📐 Dibujo de formas geométricas
- 🎨 Paleta de colores predefinida
- 💥 Detección de colisiones
- 🎬 Sistema de animación con spritesheets

## 🎮 Ejemplo Rápido

```python
import orangypy as op

# Crear ventana
op.crear_ventana(800, 600, "Mi Juego")

# Crear sprite del jugador
jugador = op.dibujar("jugador.png", 100, 100, escala=0.5)

# Definir movimientos
def mover_derecha():
    op.mover(jugador, 5, 0)

def mover_izquierda():
    op.mover(jugador, -5, 0)

# Asignar controles
op.cuando_tecla("d", mover_derecha)
op.cuando_tecla("a", mover_izquierda)

# Iniciar el juego
op.loop()
```

## 📚 Documentación

Visita la carpeta `/docs` para documentación detallada sobre:
- [Sprites y Animaciones](docs/sprites.md)
- [Sistema de Audio](docs/audio.md)
- [Control de Entrada](docs/input.md)
- [Formas Geométricas](docs/shapes.md)
- [Colores](docs/colors.md)
- [Tutorial Completo](docs/tutorial.md)

## 🎓 Tutorial Básico

1. **Crear una Ventana**
```python
op.crear_ventana(800, 600, "Mi Juego")
```

2. **Agregar un Sprite**
```python
mi_sprite = op.dibujar("imagen.png", x=100, y=100)
```

3. **Mover el Sprite**
```python
op.mover(mi_sprite, dx=5, dy=0)  # Mover 5 píxeles a la derecha
```

4. **Agregar Controles**
```python
op.cuando_tecla("SPACE", mi_funcion)
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor, lee [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.