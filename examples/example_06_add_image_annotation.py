"""example showing how to draw a segmentation overlay over an image"""

from pathlib import Path

import numpy as np

from paquo.images import QuPathImageType
from paquo.projects import QuPathProject

EXAMPLE_PROJECT = Path(__file__).parent.absolute() / "projects" / "example_06_project"
EXAMPLE_IMAGE = Path(__file__).parent.absolute() / "images" / "image_1.svs"


def segmentation_mask(h: int, w: int, r: int) -> np.typing.NDArray:
    """A circular mask with the center at top-left corner and radius `r`."""
    coords = np.moveaxis(np.indices((h, w)), 0, -1)
    boundary_mask = np.hypot(coords[..., 0], coords[..., 1]) > r
    onehot_mask = np.eye(2, dtype=np.int64)[boundary_mask.astype(np.uint8)].transpose(
        2, 0, 1
    )
    return onehot_mask


with QuPathProject(EXAMPLE_PROJECT, mode="x") as qp:
    print("created", qp.name)
    # add an image
    entry = qp.add_image(EXAMPLE_IMAGE, image_type=QuPathImageType.BRIGHTFIELD_H_E)

    tile_size = 50
    img_width = entry.width
    img_height = entry.height
    print(f"(W, H): {img_width}, {img_height}")

    # segmentation: usually, one would use the image as input to calculate the
    # segmentation mask, this is a dummy example
    mask = segmentation_mask(img_height, img_width, 1024)
    print(f"mask : {mask.shape}")

    # by default, the mask orign (top-left) is at (0, 0), but can be changed
    img_annotation = entry.hierarchy.add_image_annotation(
        mask, labels=["inside", "outside"], x=0, y=0
    )

    print(
        f"done. Please look at {qp.name} in QuPath and press F to fill the mask."
    )
