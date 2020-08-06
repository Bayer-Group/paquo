"""example showing how to create a project with annotations"""
from pathlib import Path
from paquo.projects import QuPathProject
from paquo.images import QuPathImageType
from shapely.geometry import Point, Polygon, LineString

EXAMPLE_PROJECT = Path(__file__).parent.absolute() / "projects" / "example_02_project"
EXAMPLE_IMAGE = Path(__file__).parent.absolute() / "images" / "image_1.svs"

ANNOTATIONS = {
    'Annotation 1': Point(500, 500),
    'Annotation 2': Polygon.from_bounds(510, 400, 610, 600),
    'Some Other Name': LineString([[400, 400], [450, 450], [400, 425]])
}

# create a the new project
with QuPathProject(EXAMPLE_PROJECT, mode='x') as qp:
    print("created", qp.name)

    # add a new image:
    entry = qp.add_image(EXAMPLE_IMAGE, image_type=QuPathImageType.BRIGHTFIELD_H_E)

    for name, roi in ANNOTATIONS.items():
        # add the annotations without a class set
        annotation = entry.hierarchy.add_annotation(roi=roi)
        annotation.name = name

    print(f"done. Please look at {qp.name} in QuPath.")
