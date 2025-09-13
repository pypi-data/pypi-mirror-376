# Evolis SDK for Python
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF
# ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
# PARTICULAR PURPOSE.

from enum import Enum

class ReturnCode(Enum):
    """
    Return code values.
    """

    def from_int(n:int):
        """
        Create a ReturnCode enum from integer.

        Parameters
        ----------
        n: int
            Value to convert to ReturnCode.

        Returns
        -------
        ReturnCode:
            The converted value.
        """
        rc = ReturnCode.OK
        if n < 0:
            try:
                rc = ReturnCode(n)
            except ValueError:
                rc = ReturnCode.EUNDEFINED
        return rc

    OK = 0
    """ Everything is good """

    EUNDEFINED = -1
    """ An undefined error occured """

    EINTERNAL = -2
    """ An internal logic error occured """

    ECANCELLED = -3
    """ The operation was cancelled before completion """

    EDISABLED = -4
    """ The requested feature is currently disabled """

    EUNSUPPORTED = -5
    """ The requested feature is not supported by the library or the printer """

    EPARAMS = -6
    """ Some invalid parameters were provided to the API """

    ETIMEOUT = -7
    """ A timeout occured during function call """

    SESSION_ETIMEOUT = -10
    """ The printer reservation has expired """

    SESSION_EBUSY = -11
    """ The printer is in use, session detected """

    SESSION_DISABLED = -12
    """ The session management is disabled. See evolis_set_session_management() """

    SESSION_FAILED = -13
    """ An error occured while trying to reserve the printer """

    SESSION_ENABLED = -14
    """ The operation is not available when the session management is on. See evolis_set_session_management() """

    PRINT_EDATA = -20
    """ Invalid input data, check images and settings """

    PRINT_NEEDACTION = -21
    """ The printer is not ready to print. Check ribbon, cover, feeder, etc """

    PRINT_EMECHANICAL = -22
    """ A mechanical error happened during printing """

    PRINT_WAITCARDINSERT = -23
    """ Avansia only """

    PRINT_WAITCARDEJECT = -24
    """ Avansia only """

    PRINT_EUNKNOWNRIBBON = -25
    """ The GRibbonType setting missing """

    PRINT_ENOIMAGE = -26
    """ No image was provided """

    PRINT_WSETTING = -27
    """ The settings were imported from the driver and at least one could not be read """

    PRINT_EJOB = -28
    """ A print job was not created or has expired """

    PRINT_ESESSION = -29
    """ No session currently available """

    LAM_ENOCOM = -40
    """ The lamination module is missing or can't communicate with the printer """

    LAM_EDEVICE = -41
    """ The device is not a lamination module """

    LAM_ERROR = -42
    """ The lamination module indicated an error """

    LAM_EVALUE = -43
    """ The value used or returned by the lamination module doesn't match the expected format """

    MAG_ERROR = -50
    """ Error reading or writing magnetic data """

    MAG_EDATA = -51
    """ The data intended to be written to the magnetic track is not valid """

    MAG_EBLANK = -52
    """ The magnetic track is blank """

    PRINTER_ENOCOM = -60
    """ The printer is offline """

    PRINTER_EREPLY = -61
    """ The printer reply contains "ERR" """

    PRINTER_EOTHER = -62
    """ macOS only. USB printer in use by other software """

    PRINTER_EBUSY = -63
    """ macOS only. CUPS is printing """

    PRINTER_NOSTATUS = -64
    """ Statuses are disabled on the printer """

    PRINTER_EMODEL = -65
    """ The printer model is invalid """

    PRINTER_NETWORK_ERROR = -80
    """ An error occured during network operation """

    PRINTER_NETWORK_ECERT = -81
    """ The certificate is invalid """

    CARD_ERROR = -200
    """ An error occured during card movement """

    CARD_EINSERTION = -201
    """ An error occured during card insertion """

    SMART_ERROR = -300
    """ An error occured during a smart operation """

    SMART_ENOCOM = -301
    """ Failed to communicate with the PCSC reader """

    SMART_ENOCARD = -302
    """ No smart card present to perform the reading/encoding operations """

    SMART_EBUSY = -303
    """ The card is already connected to a PCSC encoder """

    SYSTEM_ERROR = -500
    """ An error occured during an internal OS process """

    SYSTEM_EBUSY = -501
    """ The OS is currently busy """

    SYSTEM_EFILE = -502
    """ An error occured during a filesystem operation """

    USER_ERROR = -600
    """ Authentication failure """

    USER_EUNIDENTIFIED = -601
    """ No user currently logged in, authentication required """

    USER_EUNAUTHORIZED = -602
    """ The user is not authorized to perform this action """

    USER_ETIMEOUT = -603
    """ The login session expired """

    USER_EINVALID = -604
    """ Invalid login data was provided """

    SANDBOX_ERROR = -700
    """ An error occured during sandbox operation """

    SANDBOX_EBUSY = -701
    """ The sandbox is currently busy """

    SVC_ENOCOM = -10000
    """ Failed to communicate with the service """

    SVC_EREPLY = -10001
    """ Invalid service reply """

    SVC_ERROR = -10002
    """ The service indicated an error """

    SVC_EDATA = -10003
    """ The input data could not be send to the service """

    SVC_NO_EVENT = -10004
    """ No active event available for the printer """

    SVC_EEVENT = -10005
    """ The selected event is not active for the printer """

    SVC_EACTION = -10006
    """ The selected action is not active for current printer event """

    HTTP_REPLY_NOT_OK = -20000
    """ A reply was received with an HTTP error code (internal usage) """

    HTTP_EREQUEST_ERROR = -20001
    """ The HTTP request is invalid """

    HTTP_EREPLY_FORMAT = -20002
    """ The received data didn't match the expected format """

    HTTP_ERROR = -20500
    """ An unexpected HTTP communication error occured """

