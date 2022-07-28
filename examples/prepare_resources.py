"""prepare_resources.py for paquo/examples

note: this code initializes data and projects needed for
  the examples in the paquo repository. Some of it is
  copy&pasta from the pytest fixtures.

"""
import io
import itertools
import json
import pathlib
import shutil
import urllib.request

EXAMPLES_DIR = pathlib.Path(__file__).parent.absolute()
IMAGES_DIR = EXAMPLES_DIR / "images"
PROJECTS_DIR = EXAMPLES_DIR / "projects"
DATA_DIR = EXAMPLES_DIR / "data"

for example_dir in [IMAGES_DIR, PROJECTS_DIR, DATA_DIR]:
    example_dir.mkdir(parents=True, exist_ok=True)


def download_image(copies=1):
    """download the smallest aperio test image svs"""
    # openslide aperio test image
    images_base_url = "http://openslide.cs.cmu.edu/download/openslide-testdata/Aperio/"
    small_image = "CMU-1-Small-Region.svs"
    # download svs from openslide test images
    url = images_base_url + small_image
    with urllib.request.urlopen(url) as response:  # nosec B310
        buffer = io.BytesIO(response.read())
        for idx in range(copies):
            img_fn = IMAGES_DIR / f"image_{idx}.svs"
            with open(img_fn, 'wb') as out_file:
                shutil.copyfileobj(buffer, out_file)
                yield img_fn
            buffer.seek(0)


def prepare_example_resources():
    """build an example project"""
    from paquo.projects import QuPathProject
    from paquo.images import QuPathImageType
    from paquo.classes import QuPathPathClass
    from shapely.geometry import Polygon

    # download all images
    print(">>> downloading images...")
    images = list(download_image(copies=3))
    # remove the example_project
    example_project_dir = PROJECTS_DIR / "example_01_project"
    shutil.rmtree(example_project_dir, ignore_errors=True)

    print(">>> creating project...")
    with QuPathProject(example_project_dir, mode="x") as qp:
        for img_fn in images:
            qp.add_image(img_fn, image_type=QuPathImageType.BRIGHTFIELD_H_E)
        qp.path_classes = map(QuPathPathClass, ["myclass_0", "myclass_1", "myclass_2"])
        for idx, image in enumerate(qp.images):
            image.metadata['image_number'] = str(1000 + idx)

        def _get_bounds(idx_x, idx_y):
            cx = 200 * idx_x + 100
            cy = 200 * idx_y + 100
            return cx - 50, cy - 50, cx + 50, cy + 50

        image_0 = qp.images[0]
        for x, y in itertools.product(range(4), repeat=2):
            roi = Polygon.from_bounds(*_get_bounds(x, y))
            image_0.hierarchy.add_annotation(roi, path_class=QuPathPathClass("myclass_1"))

        with open(DATA_DIR / "annotations.geojson", "w") as f:
            json.dump(image_0.hierarchy.to_geojson(), f)

    print(">>> done.")


if __name__ == "__main__":
    prepare_example_resources()
