"""Primary imports: standard library and lightweight dependencies.

Loaded before runtime checks. Use delayed_imports for modules that require
graphviz, lxml, IPython (checked by run_runtime_checks).
"""
# ruff: noqa: F401 - re-exports for other modules
import os
import sys
import subprocess
import importlib
import urllib.parse
import re
import shutil
import random
import math
import webcolors
