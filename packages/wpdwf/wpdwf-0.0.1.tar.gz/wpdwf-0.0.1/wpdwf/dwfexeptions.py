
# Custom files
from wfoptionsconstants import DwfSymbolsConstants as wdsc

# Stdlib files
from os import path, mkdir

class ErrorWpFnGenericInstrument(Exception):
    """
    @Description
    This class holds errors that occured during
    runtime of an application. This one is WpFnGeneric,
    others for more specific warnings/errors need to
    derive this one. Warnings are treated as errors to
    get a smooth behaviour for each app.
    @Notes
    Resources here can expand those in py-stdlib,
    like Exception, Archive classes, Logging, 
    different Collections to manipulate data,
    preserving ultimately application state.
    """
    INFO_PARAMETER = 1
    INFO_RETURN = 2
    INFO_LIBLOADING = 3
    INFO_UNDEFINED = 4
    INFO_INSTRUMENT = 5
    
    TH_ERRLOG = 20
    
    lsStorePastErr = []
    nrLsStorePastErr = 0
    
    def __init__(self,
                 msg=""
                 ):
        # Err descriptor
        self.msg = msg
        # Nr. or entries in lsStorePastErr
        self.iMaxThSPR = ErrorWpFnGenericInstrument.TH_ERRLOG
        # File-name
        self.fName = ""
        self.locFileLog = ""

    def insertErr(self,
                  item : str
                  ) -> int:
        """
        @Description
        This method stores locally all errors to
        stream them later into a file, for example,
        to log events in case complex applications
        with digilent boards are made.
        @Parameters
        item : string with error descriptor
        @Return
        0 or 1, checkout DwfSymbolsConstants from
        WFOptionsConstants
        @Notes
        Avoid inserting too many strings, over some
        predefined threshold move lsStorePastErr
        content into a local file with custom
        format to be easy for reading.
        """
        if ErrorWpFnGenericInstrument.lsStorePastErr is None:
            # List type - incorrect
            return wdsc.WP_DWFERROR
        else:
            if ErrorWpFnGenericInstrument.nrLsStorePastErr < self.iMaxThSPR:
                # Add messages
                ErrorWpFnGenericInstrument.lsStorePastErr.append(item)
                ErrorWpFnGenericInstrument.nrLsStorePastErr += 1
            else:
                bWtF = False
                mode = ""
                # Extend file path
                if self.locFileLog != "":
                    if path.isdir(self.locFileLog) is False:
                        # 0o700 only in 3.12.4 and above of py
                        # TODO: check for permissions on other
                        # OS-sys, like MacOS, Linux.
                        mkdir(self.locFileLog, mode=0o700)
                    self.fName = self.locFileLog + self.fName
                # Extend or not self.fName file
                if path.isfile(self.fName):
                    mode = "a"
                else:
                    mode = "w"
                if ErrorWpFnGenericInstrument.nrLsStorePastErr > 0:
                    with open(self.fName, mode) as file:
                        for x in range(0, self.dimBuffer):
                            if file.write(ErrorWpFnGenericInstrument.lsStorePastErr[x]) == 0:
                                bWtF = True
                                break
                else:
                    bWtF = True
                # Reset log data
                ErrorWpFnGenericInstrument.lsStorePastErr = []
                if bWtF:
                    return wdsc.WP_DWFERROR
            return wdsc.WP_DWFSUCCESS
            
    def __repr__(self):
        """
        @Description
        Get a representative error upon throwing
        an object to avoid further problems.
        """
        return {"\nWrapper Error: {0}"
                }.format(self.msg)
