
# Custom files
from enumfuncconstants import DwfFuncCorrelationDevice
from dwfexeptions import ErrorWpFnGenericInstrument
from wfoptionsconstants import DwfSymbolsConstants as wdsc

# Stdlib files
from ctypes import (CDLL, cdll, create_string_buffer)
from ctypes import (CFUNCTYPE, POINTER, c_char,
                    c_int)
from sys import exit
from platform import system

class BindingsResources:
    def __init__(self):
        self.bVerifyRt = False

    def analyzeWinRT(self):
        pass

    def analyzeLnxRT(self):
        pass

    def analyzeMacRT(self):
        pass

class BindingsLinkUp(object):
    """
    @Description
    This class makes a self contained object
    through which dynamic lib (dwf) can be viewed in any
    py script as a unitary entity. Classes deriving this
    one can hook up to one device at a time, so multiple
    classes can have access to more devices, this approach
    is to insist on concurrent use of at least 2x devices
    from AD/ADP line-up.
    @Notes
    hard-coded path and name of lib
    or C:\\Windows\\System32\\dwf.dll
    64-bit wf installed in prog files x86 (wierd).
    paths:
        On win: "C:\\Windows\\System32\\dwf.dll"
        On lnx: ""
        On mac: ""
    Waveforms' runtime should be checked before loading into
    py, so read in binary format the file and verify it
    with some hashing functions maybe? or other algorithms
    that can certify the integrity of the file basically.
    """
    
    pathWin_WFLib = "C:\\Program Files (x86)\\Digilent\\WaveForms3\\dwf.dll"
    # The version of py used is on 64-bit though.
    pathLnx_WFLib = "/usr/lib/libdwf.so.x.x.x"
    pathMac_WFLib = "/Library/Frameworks/dwf.framework"
    # Encapsulate this resource more ... in a .pyd file maybe
    resDwf = None
    # Constants for LinkUp resource
    BLU_ERRSYSTEM = 6
    # String <-> value should be correlated,
    # maybe with a tuple/set ? () or smth ... ???
    sBLU_ERRSYSTEM = "Platform has not been found"

    def __init__(self):
        self.resourceChecker = BindingsResources()
        self.efcFnCorrGet = DwfFuncCorrelationDevice
        self._lsErrContent = ErrorWpFnGenericInstrument()
        self.libVersionDwf = ""
        # Extraction from dynamic lib, automatically set local variables
        # Below code is the most important, this part should be
        # abstracted even more from the user to avoid any
        # complications. This class should be in a separate file (.py(c/d)).
        try:
            if BindingsLinkUp.resDwf is None:
                plTarget = system()
                # Use the same linkup.
                if plTarget == "Windows":
                    # Check here the integrity of library.
                    BindingsLinkUp.resDwf = cdll.LoadLibrary(BindingsLinkUp.pathWin_WFLib)
                # WpFnGeneric lnx distro, freedesktop_os_release()
                # can be used to get more details.
                elif plTarget == "Linux" or plTarget == "Solaris":
                    # Check here the integrity of library.
                    BindingsLinkUp.resDwf = CDLL(BindingsLinkUp.pathLnx_WFLib)
                elif plTarget == "Darwin":
                    # Check here the integrity of library.
                    BindingsLinkUp.resDwf = CDLL(BindingsLinkUp.pathMac_WFLib)
                else:
                    # Store in a mechanism warnings/errors, uncertanties
                    # that can lead to undefined behaviour.
                    if self._lsErrContent.insertErr(sBLU_ERRSYSTEM) == wdsc.WP_DWFERROR:
                        sys.exit(1)
        except OSError as err:
            # Store errors in a separated list/file/logsys.
            if self._lsErrContent.insertErr(err) == wdsc.WP_DWFERROR:
                sys.exit(1)
            else:
                BindingsLinkUp.resDwf = None
                # Centralize warnings/errors, transform in some sort of audit.
                self._lsErrContent.insertErr(
                    "Unusable dwf resource - unable to load dynamic lib"
                    )
        # Common attributes for Digital/Analog instruments, System.
        self.dtFuncResDwfBLU = {
            self.efcFnCorrGet.cFDwfGetLastError : BindingsLinkUp.resDwf.FDwfGetLastError,
            self.efcFnCorrGet.cFDwfGetLastErrorMsg : BindingsLinkUp.resDwf.FDwfGetLastErrorMsg,
            self.efcFnCorrGet.cFDwfGetVersion : BindingsLinkUp.resDwf.FDwfGetVersion
        }
        # Attr :
        self.err = c_int(0)
        self.sErr = create_string_buffer(b"", size=512)
        self.sVer = create_string_buffer(b"", size=32)

    @property
    def lsErrContent(self):
        """ Get reference for self._lsErrContent """
        return self._lsErrContent

    def WpDwfGetLastError(self,
                          dwferc : POINTER(c_int)
                          ) -> int:
        """
        @Description
        Find the last encountered error, this can be:
        NoErc, UnknownError, ApiLockTimeout, AlreadyOpened,
        NotSupported, InvalidParameter0, InvalidParameter1,
        InvalidParameter2, InvalidParameter3, InvalidParameter4.
        Their representative values can be found in WFOptionsConstants
        or the header file dwf.h installed with waveforms.
        @Parameters
        dwferc : This reference is modified
                 with the corresponding error code,
                 it can be found in DwfSymbolsConstants
                 from WFOptionsConstants.py.
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        Maybe use byref(obj) instead of POINTER class.
        """
        @CFUNCTYPE(c_int, POINTER(c_int))
        def WpFnGeneric(dwferc) -> int:
            iretVal = self.dtFuncResDwfBLU.get(
                        self.efcFnCorrGet.cFDwfGetLastError
                      )(dwferc)
            return iretVal
        return WpFnGeneric(dwferc)

    def WpDwfGetLastErrorMsg(self,
                             szError : POINTER(c_char)
                             ) -> int:
        """
        @Description
        Similar to WpDwfGetLastError, but it changes
        its parameter, offering a strings instead of
        some value.
        @Parameters
        szError : Address of a passed by reference vector
                  that contains preallocated memory to
                  store characters.
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        Different address can be passed though ???
        """
        @CFUNCTYPE(c_int, POINTER(c_char))
        def WpFnGeneric(szError) -> int:
            iretVal = self.dtFuncResDwfBLU.get(
                        self.efcFnCorrGet.cFDwfGetLastErrorMsg
                      )(szError)
            return iretVal
        return WpFnGeneric(szError)

    def WpDwfGetVersion(self,
                        szVersion : POINTER(c_char)
                        ) -> int:
        """
        @Description
        Receive the version of dwf.dll, x.y.z is the
        format for the most libs.
        @Parameters
        szVersion : Address of a passed by reference vector
                    that contains preallocated memory to
                    store characters.
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, POINTER(c_char))
        def WpFnGeneric(szVersion) -> int:
            iretVal = self.dtFuncResDwfBLU.get(
                        self.efcFnCorrGet.cFDwfGetVersion
                      )(szVersion)
            self.libVersionDwf = self.sVer.value.decode("utf-8")
            return iretVal
        return WpFnGeneric(szVersion)

    def __repr__(self):
        """
        @Description
        Display errors from the last device connected to. So,
        this representation of object can be used by exceptions
        or if anything else crashes to have more traceback content
        to look out for to get things working.
        @Notes
        None
        """
        if (self.WpDwfGetLastError(self.err) == wdsc.WP_DWFERROR or
            self.WpDwfGetLastErrorMsg(self.sErr) == wdsc.WP_DWFERROR or
            self.WpDwfGetVersion(self.sVer) == wdsc.WP_DWFERROR):
           self._lsErrContent.insertErr("Could not interface locally with dwf lib")
        else:
            lcStr = "\nLow Level Layer - info:"     \
                    "\n-- Last Error: {0}"          \
                    "\n-- Last Error Message: {1}"  \
                    "\n-- Dwf version: {2}"
            return lcStr.format(str(self.err.value),
                                self.sErr.value.decode("utf-8"),
                                self.sVer.value.decode("utf-8")
                                )
