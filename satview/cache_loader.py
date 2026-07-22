import os

from skyfield.api import Loader

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")

loader = Loader(CACHE_DIR)
