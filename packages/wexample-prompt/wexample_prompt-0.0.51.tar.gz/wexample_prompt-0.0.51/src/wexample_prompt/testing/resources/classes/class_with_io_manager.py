from __future__ import annotations

from wexample_helpers.decorator.base_class import base_class
from wexample_prompt.mixins.with_io_manager import WithIoManager


@base_class
class ClassWithIoManager(WithIoManager):
    """
    The minimal class with an io manager.
    """
