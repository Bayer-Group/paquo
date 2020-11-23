"""Paquo OSX app shim example"""
from setuptools import setup

setup(
    app=["PaquoOpenQpZip.py"],
    data_files=[],
    options={
        "py2app": {
            "argv_emulation": 1,
        }
    },
    setup_requires=["py2app"],
)
