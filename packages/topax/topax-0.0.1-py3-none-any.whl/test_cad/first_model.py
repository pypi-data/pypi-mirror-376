from topax.sdfs import (
    sphere,
    union,
    translate,
    intersect,
    subtract,
    scale
)

def make_part():
    return scale(subtract(sphere(0.5, [0.4, 0, 0]), sphere(0.5, x=-0.4)), 1.5)
