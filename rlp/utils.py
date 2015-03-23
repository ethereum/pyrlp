import sys
if sys.version_info.major == 2:
    from .utils_py2 import *
else:
    from .utils_py3 import *
