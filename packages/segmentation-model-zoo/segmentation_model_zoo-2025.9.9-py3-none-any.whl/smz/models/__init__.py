from .cotr import *
from .dscnet import *
from .mednext import *
from .swin_smt import *
from .umamba import *
from .waveunet import *
from .emnet import *
from .monai_zoo import *
from .segmamba import *
from .nnunet import *

try:
    from .mmseg_models import *
except ImportError:
    pass