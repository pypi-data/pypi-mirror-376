from inspect import currentframe, getframeinfo
from pathlib import Path

from hvorfra.types import PARENT, CodeLocation


def get_caller_location(depth: int = PARENT) -> CodeLocation | None:
    frame = currentframe()
    for _ in range(depth + 1):
        if frame is None:
            return None
        frame = frame.f_back
    assert frame is not None

    frame_info = getframeinfo(frame)
    positions = frame_info.positions
    if positions is None or not isinstance(positions.col_offset, int):
        return None

    return CodeLocation(
        frame.f_globals.get("__name__"),
        Path(frame_info.filename),
        frame_info.lineno,
        positions.col_offset,
    )
