# Evolis SDK for Python
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF
# ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
# PARTICULAR PURPOSE.

import ctypes

from evolis.Connection import _instr
from evolis.Connection import _outstr
from evolis.Connection import Connection
from evolis.Evolis import Evolis
from evolis.MagCoercivity import MagCoercivity
from evolis.MagFormat import MagFormat
from evolis.ReturnCode import ReturnCode
from evolis.MagTrackNumber import MagTrackNumber
from functools import singledispatchmethod


class _CMagTracks(ctypes.Structure):
    _fields_ = [
        ("tracks", (ctypes.c_char * 256) * 3),
        ("formats", ctypes.c_int * 3),
        ("coercivity", ctypes.c_int),
        ("results", ctypes.c_int * 3),
        ("encode", ctypes.c_bool * 3),
    ]


class MagSession:
    __DEFAULT_TIMEOUT = 30000

    def __init__(self, connection: Connection):
        """
        Create a MagSession object from a Connection object.

        Parameters
        ----------
        connection: Connection
            The device's connection object.
        """
        if connection is None:
            raise TypeError("MagSession.__init__(): 'connection' argument is not valid.")
        self.__context = connection.get_context()
        self.__data = _CMagTracks()
        self.init()

    def init(self):
        """
        Reset magnetic settings and data.
        """
        Evolis.wrapper.evolis_mag_init(ctypes.byref(self.__data))

    def get_coercivity(self) -> MagCoercivity:
        """
        Accessor to get the coercivity value.

        Returns
        -------
        MagCoercivity
            Returns the coercivity.
        """
        return MagCoercivity.from_int(self.__data.coercivity)

    def set_coercivity(self, c: MagCoercivity):
        """
        Accessor to set the coercivity value.

        Parameters
        ----------
        c: MagCoercivity
            The coercivity value to set.
        """
        self.__data.coercivity = c.value

    @singledispatchmethod
    def get_format(self, track) -> MagFormat:
        """
        Accessor to get format of a track.

        Parameters
        ----------
        track: int or MagTrackNumber
            Track number (0, 1 or 2) or MagTrackNumber (TRACK1, TRACK2 or TRACK3)
        """
        raise TypeError(f"Unsupported type : {type(track)}")

    @get_format.register
    def _(self, track: int):
        """
        Accessor to get format of a track.

        Parameters
        ----------
        track: int
            Track number (0, 1 or 2).
        """
        if track >= 0 and track <= 2:
            return MagFormat.from_int(self.__data.formats[track])
        return MagFormat.UNKNOWN

    @get_format.register
    def _(self, track: MagTrackNumber):
        """
        Accessor to get format of a track.

        Parameters
        ----------
        track: MagTrackNumber
            MagTrackNumber (TRACK1, TRACK2 or TRACK3).
        """
        if track != None:
            return MagFormat.from_int(self.__data.formats[track.value])
        return MagFormat.UNKNOWN

    @singledispatchmethod
    def set_format(self, track, format: MagFormat):
        """
        Accessor to set format of a track.

        Parameters
        ----------
        track: int or MagTrackNumber
            Track number (0, 1 or 2) or MagTrackNumber (TRACK1, TRACK2 or TRACK3)

        format: MagFormat
            The value to set.
        """
        raise TypeError(f"Unsupported type : {type(track)}")

    @set_format.register
    def _(self, track: int, format: MagFormat):
        """
        Accessor to set format of a track.

        Parameters
        ----------
        track: int
            Track number (0, 1 or 2).

        format: MagFormat
            The value to set.
        """
        if track >= 0 and track <= 2:
            self.__data.formats[track] = format.value

    @set_format.register
    def _(self, track: MagTrackNumber, format: MagFormat):
        """
        Accessor to set format of a track.

        Parameters
        ----------
        track: MagTrackNumber
            MagTrackNumber (TRACK1, TRACK2 or TRACK3).

        format: MagFormat
            The value to set.
        """
        if track != None:
            self.__data.formats[track.value] = format.value

    @singledispatchmethod
    def get_data(self, track) -> str:
        """
        Accessor to get value of a track.
        You must first call read() method to retrieve magnetic
        data from the card.

        Parameters
        ----------
        track: int or MagTrackNumber
            Track number (0, 1 or 2) or MagTrackNumber (TRACK1, TRACK2 or TRACK3)

        Returns
        -------
        str
            Returns the track value.
        """
        raise TypeError(f"Unsupported type : {type(track)}")

    @get_data.register
    def _(self, track: int) -> str:
        """
        Accessor to get value of a track.
        You must first call read() method to retrieve magnetic
        data from the card.

        Parameters
        ----------
        track: int
            Track number (0, 1 or 2).

        Returns
        -------
        str
            Returns the track value.
        """
        return _outstr(self.__data.tracks[track].value)

    @get_data.register
    def _(self, track: MagTrackNumber) -> str:
        """
        Accessor to get value of a track.
        You must first call read() method to retrieve magnetic
        data from the card.

        Parameters
        ----------
        track: MagTrackNumber
            MagTrackNumber (TRACK1, TRACK2 or TRACK3).

        Returns
        -------
        str
            Returns the track value.
        """
        return _outstr(self.__data.tracks[track.value].value)

    @singledispatchmethod
    def get_status(self, track) -> ReturnCode:
        """
        Return status for a specific track of last read/write
        operation.

        Parameters
        ----------
        track: int or MagTrackNumber
            Track number (0, 1 or 2) or MagTrackNumber (TRACK1, TRACK2 or TRACK3)

        Returns
        -------
        ReturnCode
            The track i/o status.
        """
        raise TypeError(f"Unsupported type : {type(track)}")

    @get_status.register
    def _(self, track: int) -> ReturnCode:
        """
        Return status for a specific track of last read/write
        operation.

        Parameters
        ----------
        track: int
            Track number (0, 1, 2).

        Returns
        -------
        ReturnCode
            The track i/o status.
        """
        if track >= 0 and track <= 2:
            return ReturnCode.from_int(self.__data.results[track])
        return ReturnCode.EUNDEFINED

    @get_status.register
    def _(self, track: MagTrackNumber) -> ReturnCode:
        """
        Return status for a specific track of last read/write
        operation.

        Parameters
        ----------
        track: MagTrackNumber
            MagTrackNumber (TRACK1, TRACK2 or TRACK3)

        Returns
        -------
        ReturnCode
            The track i/o status.
        """
        if track != None:
            return ReturnCode.from_int(self.__data.results[track.value])
        return MagFormat.UNKNOWN

    @singledispatchmethod
    def set_track(self, track, format: MagFormat, data: str):
        """
        Set track format and data. In-memory operation.
        Nothing is sent to the printer here.

        Parameters
        ----------
        track: int or MagTrackNumber
            Track number (0, 1 or 2) or MagTrackNumber (TRACK1, TRACK2 or TRACK3)

        format: MagFormat
            The format to set for the track.

        data: str
            Data to write on the track.
        """
        raise TypeError(f"Unsupported type : {type(track)}")

    @set_track.register
    def _(self, track: int, format: MagFormat, data: str):
        """
        Set track format and data. In-memory operation.
        Nothing is sent to the printer here.

        Parameters
        ----------
        track: int
            Track number (0, 1 or 2).

        format: MagFormat
            The format to set for the track.

        data: str
            Data to write on the track.
        """
        Evolis.wrapper.evolis_mag_set_track(ctypes.byref(self.__data), track, format.value, _instr(data))

    @set_track.register
    def _(self, track: MagTrackNumber, format: MagFormat, data: str):
        """
        Set track format and data. In-memory operation.
        Nothing is sent to the printer here.

        Parameters
        ----------
        track: MagTrackNumber
            MagTrackNumber (TRACK1, TRACK2 or TRACK3)

        format: MagFormat
            The format to set for the track.

        data: str
            Data to write on the track.
        """
        Evolis.wrapper.evolis_mag_set_track(ctypes.byref(self.__data), track.value, format.value, _instr(data))

    def write(self, timeout_ms: int = __DEFAULT_TIMEOUT) -> ReturnCode:
        """
        Writes magnetic data, configured with set_track() method, to
        the card. Card is inserted from input tray if no card present
        in the printer.

        Parameters
        ----------
        timeout_ms: int
            Specify a maximum duration, in milliseconds, for the function to
            wait for a response from the printer.

        Returns
        -------
        ReturnCode
            A ReturnCode value.
        """
        return ReturnCode.from_int(
            Evolis.wrapper.evolis_mag_writet(self.__context, ctypes.byref(self.__data), timeout_ms)
        )

    def read(self, timeout_ms: int = __DEFAULT_TIMEOUT) -> ReturnCode:
        """
        Reads all mag tracks from the card.
        Card is inserted from input tray if
        no card present in the printer.

        To read only one or two specific track(s)
        please use read_tracks().

        Parameters
        ----------
        timeout_ms: int
            Specify a maximum duration, in milliseconds, for the function to
            wait for a response from the printer.

        Returns
        -------
        ReturnCode
            A ReturnCode value. Track data can be retrieved with a
            call to get_data().
        """
        return ReturnCode.from_int(
            Evolis.wrapper.evolis_mag_readt(self.__context, ctypes.byref(self.__data), timeout_ms)
        )

    def read_tracks(self, t0: bool, t1: bool, t2: bool, timeout_ms: int = __DEFAULT_TIMEOUT) -> ReturnCode:
        """
        Reads one or more mag track(s) from the card.
        Card is inserted from input tray if
        no card present in the printer.

        Parameters
        ----------
        t0: bool
            True to read 1st track.

        t1: bool
            True to read 2nd track.

        t2: bool
            True to read 3rd track.

        timeout_ms: int
            Specify a maximum duration, in milliseconds, for the function to
            wait for a response from the printer.

        Returns
        -------
        ReturnCode
            A ReturnCode value. Track data can be retrieved with a
            call to get_data().
        """
        return ReturnCode.from_int(
            Evolis.wrapper.evolis_mag_read_trackst(self.__context, ctypes.byref(self.__data), t0, t1, t2, timeout_ms)
        )
