# Evolis SDK for Python
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF
# ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
# PARTICULAR PURPOSE.

from enum import Enum

class MagTrackNumber(Enum):
    """
    Magnetic track number.
    """

    @staticmethod
    def from_int(v: int):
        try:
            return MagTrackNumber(v)
        except TypeError:
            return MagTrackNumber.TRACK1

    TRACK1 = 0 # First magnetic track

    TRACK2 = 1 # Second magnetic track

    TRACK3 = 2 # Third magnetic track
