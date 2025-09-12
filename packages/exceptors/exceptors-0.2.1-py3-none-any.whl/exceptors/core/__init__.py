from typing import *

from catchlib import Catcher

__all__ = ["Exceptor"]


class Exceptor(Catcher): ...


Exceptor.capture = Exceptor.catch
Exceptor.captured = Exceptor.caught
