"""example showing how to read annotations from an existing project"""
from pathlib import Path
from paquo.projects import QuPathProject

EXAMPLE_PROJECT = Path(__file__).parent.absolute() / "projects" / "example_01_project"

# read the project and raise Exception if it's not there
with QuPathProject(EXAMPLE_PROJECT, mode='r') as qp:
    print("opened", qp.name)
    # iterate over the images
    for image in qp.images:
        # annotations are accessible via the hierarchy
        annotations = image.hierarchy.annotations

        print("Image", image.image_name, "has", len(annotations), "annotations.")
        for annotation in annotations:
            # annotations are paquo.pathobjects.QuPathPathAnnotationObject instances
            # their ROIs are accessible as shapely geometries via the .roi property
            print("> class:", annotation.path_class.name, "roi:", annotation.roi)

    print("done")
