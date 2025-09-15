from typing import Optional
from .streams import StreamSpecifier
from abc import ABC, abstractmethod
from ..utils.commons import build_flags


class BaseInput(ABC):
    def __init__(self, stream_type: Optional[str] = None) -> None:
        self.flags = {}
        self.stream_type = stream_type

    @abstractmethod
    def _build_input_flags(self) -> list[str]:
        raise NotImplementedError()

    def _build(self):
        return build_flags(self.flags)

    def _get_outputs(self):
        return StreamSpecifier(self)
