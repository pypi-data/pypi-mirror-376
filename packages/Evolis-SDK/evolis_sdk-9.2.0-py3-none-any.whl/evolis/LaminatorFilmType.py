# Evolis SDK for Python
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF
# ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
# PARTICULAR PURPOSE.

from enum import Enum

class LaminatorFilmType(Enum):
    """
    List of laminator films accepted by Evolis laminators.
    """

    def from_int(n:int):
        try:
            return LaminatorFilmType(n)
        except ValueError:
            return LaminatorFilmType.UNKNOWN

    UNKNOWN = 0
    CLEAR_PATCH_1_0_MIL = 500
    GENERIC_HOLO_PATCH_1_0_MIL = 501
    CLEAR_SMART_CUT_PATCH_1_0_MIL = 502
    CLEAR_MAG_CUT_PATCH_1_0_MIL = 503
    CLEAR_PATCH_0_5_MIL = 504
    GENERIC_HOLO_PATCH_0_6_MIL = 505
    CLEAR_SMART_CUT_PATCH_0_5_MIL = 506
    CLEAR_MAG_CUT_PATCH_0_5_MIL = 507
    GENERIC_HOLO_CONTINUOUS = 508
    GENERIC_HOLO_REGISTERED = 509
    CLEAR_VARNISH = 510
    ALT_SMART_FULL_1_0_MIL = 511
    ALT_SMART_MAG_1_0_MIL = 512
    ALT_FULL_MAG_1_0_MI = 513
