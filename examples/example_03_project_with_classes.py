"""example showing how to create a empty project with classes"""
from pathlib import Path
from paquo.projects import QuPathProject
from paquo.classes import QuPathPathClass

EXAMPLE_PROJECT = Path(__file__).parent.absolute() / "projects" / "example_03_project"

MY_CLASSES_AND_COLORS = [
    ("My Class 1", "#ff0000"),
    ("Some Other Class", "#0000ff"),
    ("Nothing*", "#00ff00"),
]

# create a the new project
with QuPathProject(EXAMPLE_PROJECT, mode='x') as qp:
    print("created", qp.name)

    new_classes = []
    for class_name, class_color in MY_CLASSES_AND_COLORS:
        new_classes.append(
            QuPathPathClass(name=class_name, color=class_color)
        )

    # setting QuPathProject.path_class always replaces all classes
    qp.path_classes = new_classes
    print("project classes:")
    for path_class in qp.path_classes:
        print(">", f"'{path_class.name}'", path_class.color.to_hex())

    print(f"done. Please look at {qp.name} in QuPath.")
