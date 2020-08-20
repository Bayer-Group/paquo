"""example showing how to create a project with image metadata"""
from pathlib import Path
from paquo.projects import QuPathProject
from paquo.images import QuPathImageType

EXAMPLE_PROJECT = Path(__file__).parent.absolute() / "projects" / "example_04_project"
EXAMPLE_IMAGE_DIR = Path(__file__).parent.absolute() / "images"

METADATA = {
    "image_0.svs": {
        "annotator": "Alice",
        "status": "finished",
        "diagnosis": "healthy",
    },
    "image_1.svs": {
        "annotator": "Bob",
        "status": "started",
        "diagnosis": "sick",
    },
    "image_2.svs": {
        "annotator": "Chuck",
        "status": "waiting",
        "diagnosis": "unknown",
    },
}

# create a the new project
with QuPathProject(EXAMPLE_PROJECT, mode='x') as qp:
    print("created", qp.name)

    for image_fn, metadata in METADATA.items():
        entry = qp.add_image(
            EXAMPLE_IMAGE_DIR / image_fn,
            image_type=QuPathImageType.BRIGHTFIELD_H_E
        )
        # entry.metadata is a dict-like proxy:
        # > entry.metadata[key] = value
        # > entry.metadata.update(new_dict)
        # > etc...
        entry.metadata = metadata

    print(f"done. Please look at {qp.name} in QuPath. And look at he Project Metadata.")
