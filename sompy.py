# This file is used to add sompy/somutil to the sys.path
from sys import path as syspath
from os.path import dirname, abspath, join
sompy_path = abspath(join(dirname(__file__), 'submodules/sompy/somutil'))
if sompy_path not in syspath:
    syspath.insert(0, sompy_path)
