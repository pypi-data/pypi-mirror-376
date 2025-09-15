import sys
from typing import Any, Optional
from ..material.styles import useTheme
from .use_media_query import useMediaQuery
from qtmui.lib.qtcompat.QtWidgets import QApplication
from qtmui.lib.qtcompat.QtCore import QSize
from qtmui.hooks.use_state import useState, State
def get_screen_size(): ...
def ___useResponsive(size: int, query: str, start: Optional[Any], end: Optional[Any]): ...
def useResponsive(query: str, start: Optional[Any], end: Optional[Any]): ...