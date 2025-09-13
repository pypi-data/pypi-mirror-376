__all__ = [
    'UserFont',
    'butterfly',
    'escher',
    'goblin_virus',
    'register_userfont',
    'userfont',
]

import PIL.Image

from .userfont import userfont, register_userfont, UserFont

def butterfly() -> PIL.Image.ImageFile.ImageFile: ...
def escher() -> PIL.Image.ImageFile.ImageFile: ...
def goblin_virus() -> PIL.Image.ImageFile.ImageFile: ...
