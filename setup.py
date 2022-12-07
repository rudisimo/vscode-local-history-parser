#!/usr/bin/env python
import os

from setuptools import setup


if __name__ == "__main__":
    BASEDIR = os.path.dirname(__file__)
    BASEDIR and os.chdir(BASEDIR)
    setup()
