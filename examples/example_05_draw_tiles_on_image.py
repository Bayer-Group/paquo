"""example showing how to draw a tile detection overlay over an image"""
import itertools
import math
import random
from pathlib import Path
from typing import Tuple, Iterator

from shapely.geometry import Polygon

from paquo.images import QuPathImageType
from paquo.projects import QuPathProject

EXAMPLE_PROJECT = Path(__file__).parent.absolute() / "projects" / "example_05_project"
EXAMPLE_IMAGE = Path(__file__).parent.absolute() / "images" / "image_1.svs"


def measurement(x, y, w, h, a=8) -> float:
    """some measurement that you want to display"""
    v = math.exp(-a * ((2 * x / w - 1) ** 2 + (2 * y / h - 1) ** 2))
    v += random.uniform(-0.1, 0.1)
    return min(max(0., v), 1.)


def iterate_grid(width, height, grid_size) -> Iterator[Tuple[int, int]]:
    """return corner x,y coordinates for a grid"""
    yield from itertools.product(
        range(0, width, grid_size),
        range(0, height, grid_size)
    )


with QuPathProject(EXAMPLE_PROJECT, mode='x') as qp:
    print("created", qp.name)
    # add an image
    entry = qp.add_image(
        EXAMPLE_IMAGE,
        image_type=QuPathImageType.BRIGHTFIELD_H_E
    )

    tile_size = 50
    img_width = entry.width
    img_height = entry.height

    # iterate over the image in a grid pattern
    for x0, y0 in iterate_grid(img_width, img_height, grid_size=tile_size):
        tile = Polygon.from_bounds(x0, y0, x0 + tile_size, y0 + tile_size)
        # add tiles (tiles are specialized detection objects drawn without border)
        detection = entry.hierarchy.add_tile(
            roi=tile,
            measurements={
                'measurement': measurement(x0, y0, img_width, img_height)
            }
        )

    print("added", len(entry.hierarchy.detections), "tiles")
    print(f"done. Please look at {qp.name} in QuPath and look at 'Measure > Show Measurement Maps'")
