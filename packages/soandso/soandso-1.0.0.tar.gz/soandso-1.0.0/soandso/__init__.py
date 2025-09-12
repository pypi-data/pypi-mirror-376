"""
soandso - A collection of delightfully arbitrary utilities
"""

__version__ = "1.0.0"
__author__ = "Kohan Mathers"
__email__ = "mathers.kohan@gmail.com"

from .core import do_a_thing, do_another_thing, do_something_else
from .utils import make_it_fancy, count_stuff, generate_nonsense

__all__ = [
    "do_a_thing",
    "do_another_thing", 
    "do_something_else",
    "make_it_fancy",
    "count_stuff",
    "generate_nonsense"
]