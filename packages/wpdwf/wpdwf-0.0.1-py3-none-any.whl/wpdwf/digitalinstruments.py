
# Custom files
from wfoptionsconstants import DwfSymbolsConstants as wdsc
from enumfuncconstants import DwfFuncCorrelationDigital
from wfoptionsconstants import (DwfSymbolsConstants, DwfFnParamOpt)
from dwfresource import BindingsLinkUp
from dwfexeptions import ErrorWpFnGenericInstrument

# Stdlib file(s)
from ctypes import (CFUNCTYPE, POINTER, c_char,
                    c_int, c_ubyte, create_string_buffer,
                    c_uint, c_double, c_ulonglong,
                    c_ushort, c_void_p)
#from ctypes._endian import _other_endian
#from ctypes import Array

class DigitalIO:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationDigital.cFDwfDigitalIOReset, # Control
            DwfFuncCorrelationDigital.cFDwfDigitalIOConfigure,
            DwfFuncCorrelationDigital.cFDwfDigitalIOStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableInfo, # Configure
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableSet,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableGet,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputSet,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputGet,
            DwfFuncCorrelationDigital.cFDwfDigitalIOPullInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalIOPullSet,
            DwfFuncCorrelationDigital.cFDwfDigitalIOPullGet,
            DwfFuncCorrelationDigital.cFDwfDigitalIODriveInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalIODriveSet,
            DwfFuncCorrelationDigital.cFDwfDigitalIODriveGet,
            DwfFuncCorrelationDigital.cFDwfDigitalIOInputInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalIOInputStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableInfo64,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableSet64,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableGet64,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputInfo64,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputSet64,
            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputGet64,
            DwfFuncCorrelationDigital.cFDwfDigitalIOInputInfo64,
            DwfFuncCorrelationDigital.cFDwfDigitalIOInputStatus64
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfDigitalIOReset, # Control
            BindingsLinkUp.resDwf.FDwfDigitalIOConfigure,
            BindingsLinkUp.resDwf.FDwfDigitalIOStatus,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputEnableInfo, # Configure
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputEnableSet,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputEnableGet,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputInfo,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputSet,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputGet,
            BindingsLinkUp.resDwf.FDwfDigitalIOPullInfo,
            BindingsLinkUp.resDwf.FDwfDigitalIOPullSet,
            BindingsLinkUp.resDwf.FDwfDigitalIOPullGet,
            BindingsLinkUp.resDwf.FDwfDigitalIODriveInfo,
            BindingsLinkUp.resDwf.FDwfDigitalIODriveSet,
            BindingsLinkUp.resDwf.FDwfDigitalIODriveGet,
            BindingsLinkUp.resDwf.FDwfDigitalIOInputInfo,
            BindingsLinkUp.resDwf.FDwfDigitalIOInputStatus,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputEnableInfo64,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputEnableSet64,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputEnableGet64,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputInfo64,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputSet64,
            BindingsLinkUp.resDwf.FDwfDigitalIOOutputGet64,
            BindingsLinkUp.resDwf.FDwfDigitalIOInputInfo64,
            BindingsLinkUp.resDwf.FDwfDigitalIOInputStatus64
        ]
        self._dtFuncDIO = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncDIO) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncDIO[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncDIO(self) -> dict:
        """ Get reference for self._dtFuncDIO """
        return self._dtFuncDIO

class LogicAnalyzer:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationDigital.cFDwfDigitalInReset, # Control and status
            DwfFuncCorrelationDigital.cFDwfDigitalInConfigure,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusSamplesLeft,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusSamplesValid,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusIndexWrite,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusAutoTriggered,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusData,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusData2,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusData3,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusNoise2,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusNoise3,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusRecord,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusCompress,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusCompressed,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusCompressed2,
            DwfFuncCorrelationDigital.cFDwfDigitalInStatusTime,
            DwfFuncCorrelationDigital.cFDwfDigitalInCounterInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInCounterSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInCounterGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInCounterStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalInInternalClockInfo, # Acquisition configuration
            DwfFuncCorrelationDigital.cFDwfDigitalInClockSourceInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInClockSourceSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInClockSourceGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInDividerInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInDividerSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInDividerGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInBitsInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInSampleFormatSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInSampleFormatGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInInputOrderSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInBufferSizeInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInBufferSizeSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInBufferSizeGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInBuffersInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInBuffersSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInBuffersGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInBuffersStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalInSampleModeInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInSampleModeSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInSampleModeGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInSampleSensibleSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInSampleSensibleGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInAcquisitionModeInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInAcquisitionModeSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInAcquisitionModeGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSourceSet, # Trigger configuration
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSourceGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSlopeSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSlopeGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPositionInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPositionSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPositionGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPrefillSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPrefillGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerAutoTimeoutInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerAutoTimeoutSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerAutoTimeoutGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerGet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerInfo64,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSet64,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerGet64,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerResetSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerResetSet64,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerCountSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerLengthSet,
            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerMatchSet
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfDigitalInReset, # Control and status
            BindingsLinkUp.resDwf.FDwfDigitalInConfigure,
            BindingsLinkUp.resDwf.FDwfDigitalInStatus,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusSamplesLeft,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusSamplesValid,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusIndexWrite,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusAutoTriggered,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusData,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusData2,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusData3,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusNoise2,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusNoise3,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusRecord,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusCompress,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusCompressed,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusCompressed2,
            BindingsLinkUp.resDwf.FDwfDigitalInStatusTime,
            BindingsLinkUp.resDwf.FDwfDigitalInCounterInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInCounterSet,
            BindingsLinkUp.resDwf.FDwfDigitalInCounterGet,
            BindingsLinkUp.resDwf.FDwfDigitalInCounterStatus,
            BindingsLinkUp.resDwf.FDwfDigitalInInternalClockInfo, # Acquisition configuration
            BindingsLinkUp.resDwf.FDwfDigitalInClockSourceInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInClockSourceSet,
            BindingsLinkUp.resDwf.FDwfDigitalInClockSourceGet,
            BindingsLinkUp.resDwf.FDwfDigitalInDividerInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInDividerSet,
            BindingsLinkUp.resDwf.FDwfDigitalInDividerGet,
            BindingsLinkUp.resDwf.FDwfDigitalInBitsInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInSampleFormatSet,
            BindingsLinkUp.resDwf.FDwfDigitalInSampleFormatGet,
            BindingsLinkUp.resDwf.FDwfDigitalInInputOrderSet,
            BindingsLinkUp.resDwf.FDwfDigitalInBufferSizeInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInBufferSizeSet,
            BindingsLinkUp.resDwf.FDwfDigitalInBufferSizeGet,
            BindingsLinkUp.resDwf.FDwfDigitalInBuffersInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInBuffersSet,
            BindingsLinkUp.resDwf.FDwfDigitalInBuffersGet,
            BindingsLinkUp.resDwf.FDwfDigitalInBuffersStatus,
            BindingsLinkUp.resDwf.FDwfDigitalInSampleModeInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInSampleModeSet,
            BindingsLinkUp.resDwf.FDwfDigitalInSampleModeGet,
            BindingsLinkUp.resDwf.FDwfDigitalInSampleSensibleSet,
            BindingsLinkUp.resDwf.FDwfDigitalInSampleSensibleGet,
            BindingsLinkUp.resDwf.FDwfDigitalInAcquisitionModeInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInAcquisitionModeSet,
            BindingsLinkUp.resDwf.FDwfDigitalInAcquisitionModeGet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerSourceSet, # Trigger configuration
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerSourceGet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerSlopeSet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerSlopeGet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerPositionInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerPositionSet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerPositionGet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerPrefillSet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerPrefillGet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerAutoTimeoutInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerAutoTimeoutSet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerAutoTimeoutGet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerInfo,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerSet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerGet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerInfo64,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerSet64,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerGet64,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerResetSet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerResetSet64,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerCountSet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerLengthSet,
            BindingsLinkUp.resDwf.FDwfDigitalInTriggerMatchSet
        ]
        self._dtFuncLA = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncLA) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncLA[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncLA(self) -> dict:
        """ Get reference for self._dtFuncLA """
        return self._dtFuncLA

class PatternGenerator:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationDigital.cFDwfDigitalOutReset, # Control
            DwfFuncCorrelationDigital.cFDwfDigitalOutConfigure,
            DwfFuncCorrelationDigital.cFDwfDigitalOutStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalOutStatusOutput,
            DwfFuncCorrelationDigital.cFDwfDigitalOutInternalClockInfo, # Configuration
            DwfFuncCorrelationDigital.cFDwfDigitalOutTriggerSourceSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutTriggerSourceGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRunInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRunSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRunGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRunStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalOutWaitInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalOutWaitSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutWaitGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalOutTriggerSlopeSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutTriggerSlopeGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatTriggerSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatTriggerGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutCount,
            DwfFuncCorrelationDigital.cFDwfDigitalOutEnableSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutEnableGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutOutputInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalOutOutputSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutOutputGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutTypeInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalOutTypeSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutTypeGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutIdleInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalOutIdleSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutIdleGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerInitSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerInitGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterInfo,
            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterInitSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterInitGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepetitionInfo, # ADP3X50
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepetitionSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutRepetitionGet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutDataInfo, # For all boards
            DwfFuncCorrelationDigital.cFDwfDigitalOutDataSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutPlayDataSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutPlayUpdateSet,
            DwfFuncCorrelationDigital.cFDwfDigitalOutPlayRateSet
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfDigitalOutReset, # Control
            BindingsLinkUp.resDwf.FDwfDigitalOutConfigure,
            BindingsLinkUp.resDwf.FDwfDigitalOutStatus,
            BindingsLinkUp.resDwf.FDwfDigitalOutStatusOutput,
            BindingsLinkUp.resDwf.FDwfDigitalOutInternalClockInfo, # Configuration
            BindingsLinkUp.resDwf.FDwfDigitalOutTriggerSourceSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutTriggerSourceGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRunInfo,
            BindingsLinkUp.resDwf.FDwfDigitalOutRunSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRunGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRunStatus,
            BindingsLinkUp.resDwf.FDwfDigitalOutWaitInfo,
            BindingsLinkUp.resDwf.FDwfDigitalOutWaitSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutWaitGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRepeatInfo,
            BindingsLinkUp.resDwf.FDwfDigitalOutRepeatSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRepeatGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRepeatStatus,
            BindingsLinkUp.resDwf.FDwfDigitalOutTriggerSlopeSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutTriggerSlopeGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRepeatTriggerSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRepeatTriggerGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutCount,
            BindingsLinkUp.resDwf.FDwfDigitalOutEnableSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutEnableGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutOutputInfo,
            BindingsLinkUp.resDwf.FDwfDigitalOutOutputSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutOutputGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutTypeInfo,
            BindingsLinkUp.resDwf.FDwfDigitalOutTypeSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutTypeGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutIdleInfo,
            BindingsLinkUp.resDwf.FDwfDigitalOutIdleSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutIdleGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutDividerInfo,
            BindingsLinkUp.resDwf.FDwfDigitalOutDividerInitSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutDividerInitGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutDividerSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutDividerGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutCounterInfo,
            BindingsLinkUp.resDwf.FDwfDigitalOutCounterInitSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutCounterInitGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutCounterSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutCounterGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRepetitionInfo, # ADP3X50
            BindingsLinkUp.resDwf.FDwfDigitalOutRepetitionSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutRepetitionGet,
            BindingsLinkUp.resDwf.FDwfDigitalOutDataInfo, # For all boards
            BindingsLinkUp.resDwf.FDwfDigitalOutDataSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutPlayDataSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutPlayUpdateSet,
            BindingsLinkUp.resDwf.FDwfDigitalOutPlayRateSet
        ]
        self._dtFuncPG = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncPG) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncPG[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncPG(self) -> dict:
        """ Get reference for self._dtFuncPG """
        return self._dtFuncPG

class DigitalProtocols:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationDigital.cFDwfDigitalUartReset, # UART
            DwfFuncCorrelationDigital.cFDwfDigitalUartRateSet,
            DwfFuncCorrelationDigital.cFDwfDigitalUartBitsSet,
            DwfFuncCorrelationDigital.cFDwfDigitalUartParitySet,
            DwfFuncCorrelationDigital.cFDwfDigitalUartPolaritySet,
            DwfFuncCorrelationDigital.cFDwfDigitalUartStopSet,
            DwfFuncCorrelationDigital.cFDwfDigitalUartTxSet,
            DwfFuncCorrelationDigital.cFDwfDigitalUartRxSet,
            DwfFuncCorrelationDigital.cFDwfDigitalUartTx,
            DwfFuncCorrelationDigital.cFDwfDigitalUartRx,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiReset, # SPI
            DwfFuncCorrelationDigital.cFDwfDigitalSpiFrequencySet,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiClockSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiDataSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiIdleSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiModeSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiOrderSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiDelaySet,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiSelectSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiSelect,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiWriteRead,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiWriteRead16,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiWriteRead32,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiRead,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiReadOne,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiRead16,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiRead32,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiWrite,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiWriteOne,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiWrite16,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiWrite32,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWriteRead,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWriteRead16,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWriteRead32,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdRead,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdReadOne,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdRead16,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdRead32,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWrite,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWriteOne,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWrite16,
            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWrite32,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cReset, # I2C
            DwfFuncCorrelationDigital.cFDwfDigitalI2cClear,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cStretchSet,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cRateSet,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cReadNakSet,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cSclSet,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cSdaSet,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cTimeoutSet,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cWriteRead,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cRead,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cWrite,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cWriteOne,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cSpyStart,
            DwfFuncCorrelationDigital.cFDwfDigitalI2cSpyStatus,
            DwfFuncCorrelationDigital.cFDwfDigitalCanReset, # CAN
            DwfFuncCorrelationDigital.cFDwfDigitalCanRateSet,
            DwfFuncCorrelationDigital.cFDwfDigitalCanPolaritySet,
            DwfFuncCorrelationDigital.cFDwfDigitalCanTxSet,
            DwfFuncCorrelationDigital.cFDwfDigitalCanRxSet,
            DwfFuncCorrelationDigital.cFDwfDigitalCanTx,
            DwfFuncCorrelationDigital.cFDwfDigitalCanRx,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdReset, # SWD
            DwfFuncCorrelationDigital.cFDwfDigitalSwdRateSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdCkSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdIoSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdTurnSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdTrailSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdParkSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdNakSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdIoIdleSet,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdClear,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdWrite,
            DwfFuncCorrelationDigital.cFDwfDigitalSwdRead
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfDigitalUartReset, # UART
            BindingsLinkUp.resDwf.FDwfDigitalUartRateSet,
            BindingsLinkUp.resDwf.FDwfDigitalUartBitsSet,
            BindingsLinkUp.resDwf.FDwfDigitalUartParitySet,
            BindingsLinkUp.resDwf.FDwfDigitalUartPolaritySet,
            BindingsLinkUp.resDwf.FDwfDigitalUartStopSet,
            BindingsLinkUp.resDwf.FDwfDigitalUartTxSet,
            BindingsLinkUp.resDwf.FDwfDigitalUartRxSet,
            BindingsLinkUp.resDwf.FDwfDigitalUartTx,
            BindingsLinkUp.resDwf.FDwfDigitalUartRx,
            BindingsLinkUp.resDwf.FDwfDigitalSpiReset, # SPI
            BindingsLinkUp.resDwf.FDwfDigitalSpiFrequencySet,
            BindingsLinkUp.resDwf.FDwfDigitalSpiClockSet,
            BindingsLinkUp.resDwf.FDwfDigitalSpiDataSet,
            BindingsLinkUp.resDwf.FDwfDigitalSpiIdleSet,
            BindingsLinkUp.resDwf.FDwfDigitalSpiModeSet,
            BindingsLinkUp.resDwf.FDwfDigitalSpiOrderSet,
            BindingsLinkUp.resDwf.FDwfDigitalSpiDelaySet,
            BindingsLinkUp.resDwf.FDwfDigitalSpiSelectSet,
            BindingsLinkUp.resDwf.FDwfDigitalSpiSelect,
            BindingsLinkUp.resDwf.FDwfDigitalSpiWriteRead,
            BindingsLinkUp.resDwf.FDwfDigitalSpiWriteRead16,
            BindingsLinkUp.resDwf.FDwfDigitalSpiWriteRead32,
            BindingsLinkUp.resDwf.FDwfDigitalSpiRead,
            BindingsLinkUp.resDwf.FDwfDigitalSpiReadOne,
            BindingsLinkUp.resDwf.FDwfDigitalSpiRead16,
            BindingsLinkUp.resDwf.FDwfDigitalSpiRead32,
            BindingsLinkUp.resDwf.FDwfDigitalSpiWrite,
            BindingsLinkUp.resDwf.FDwfDigitalSpiWriteOne,
            BindingsLinkUp.resDwf.FDwfDigitalSpiWrite16,
            BindingsLinkUp.resDwf.FDwfDigitalSpiWrite32,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdWriteRead,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdWriteRead16,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdWriteRead32,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdRead,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdReadOne,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdRead16,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdRead32,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdWrite,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdWriteOne,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdWrite16,
            BindingsLinkUp.resDwf.FDwfDigitalSpiCmdWrite32,
            BindingsLinkUp.resDwf.FDwfDigitalI2cReset, # I2C
            BindingsLinkUp.resDwf.FDwfDigitalI2cClear,
            BindingsLinkUp.resDwf.FDwfDigitalI2cStretchSet,
            BindingsLinkUp.resDwf.FDwfDigitalI2cRateSet,
            BindingsLinkUp.resDwf.FDwfDigitalI2cReadNakSet,
            BindingsLinkUp.resDwf.FDwfDigitalI2cSclSet,
            BindingsLinkUp.resDwf.FDwfDigitalI2cSdaSet,
            BindingsLinkUp.resDwf.FDwfDigitalI2cTimeoutSet,
            BindingsLinkUp.resDwf.FDwfDigitalI2cWriteRead,
            BindingsLinkUp.resDwf.FDwfDigitalI2cRead,
            BindingsLinkUp.resDwf.FDwfDigitalI2cWrite,
            BindingsLinkUp.resDwf.FDwfDigitalI2cWriteOne,
            BindingsLinkUp.resDwf.FDwfDigitalI2cSpyStart,
            BindingsLinkUp.resDwf.FDwfDigitalI2cSpyStatus,
            BindingsLinkUp.resDwf.FDwfDigitalCanReset, # CAN
            BindingsLinkUp.resDwf.FDwfDigitalCanRateSet,
            BindingsLinkUp.resDwf.FDwfDigitalCanPolaritySet,
            BindingsLinkUp.resDwf.FDwfDigitalCanTxSet,
            BindingsLinkUp.resDwf.FDwfDigitalCanRxSet,
            BindingsLinkUp.resDwf.FDwfDigitalCanTx,
            BindingsLinkUp.resDwf.FDwfDigitalCanRx,
            BindingsLinkUp.resDwf.FDwfDigitalSwdReset, # SWD
            BindingsLinkUp.resDwf.FDwfDigitalSwdRateSet,
            BindingsLinkUp.resDwf.FDwfDigitalSwdCkSet,
            BindingsLinkUp.resDwf.FDwfDigitalSwdIoSet,
            BindingsLinkUp.resDwf.FDwfDigitalSwdTurnSet,
            BindingsLinkUp.resDwf.FDwfDigitalSwdTrailSet,
            BindingsLinkUp.resDwf.FDwfDigitalSwdParkSet,
            BindingsLinkUp.resDwf.FDwfDigitalSwdNakSet,
            BindingsLinkUp.resDwf.FDwfDigitalSwdIoIdleSet,
            BindingsLinkUp.resDwf.FDwfDigitalSwdClear,
            BindingsLinkUp.resDwf.FDwfDigitalSwdWrite,
            BindingsLinkUp.resDwf.FDwfDigitalSwdRead
        ]
        self._dtFuncDP = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncDP) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncDP[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncDP(self) -> dict:
        """ Get reference for self._dtFuncDP """
        return self._dtFuncDP

class DigitalResources:
    """
    @Description
    @Notes
    """
    def __init__(self):
        self._dio = DigitalIO()
        #self._la = LogicAnalyzer()
        #self._pg = PatternGenerator()
        self._dp = DigitalProtocols()

    @property
    def dio(self):
        """ Get reference for self._dio """
        return self._dio

#    @property
#    def la(self):
#        """ Get reference for self._la """
#        return self._la

#    @property
#    def pg(self):
#        """ Get reference for self._pg """
#        return self._pg

    @property
    def dp(self):
        """ Get reference for self._dp """
        return self._dp

class DigitalInstruments:
    """
    @Description
    This class implements access to all instruments
    similar to pattern generator, logic analyzer.
    @Notes
    None
    """

    SUCCESS = 0
    FAILURE = -1

    class IOConfig:
        """
        @Description
        Digital I/O resources for a single device are encapsulated
        here which can be used for more than one device. Its handler
        is stored then an IO instance is created, so the functions
        that are intended to be used are cntrlDigitalIODrive,
        cntrlDigitalIOInput, cntrlDigitalIOOutput and cntrlDigitalIOPull,
        these use the wrapper functions that starts with WpDwf... .
        @Notes
        Functions with the prefix WpDwf... can be used, but they
        only encapsulate ctypes library, which is of use for
        waveforms' runtime library, to use python built-in types and
        build setups independently of waveforms application.
        """
        def __init__(self,
                     iHnd : c_int
                     ):
            self.dio = DigitalIO()
            self.dtFuncDIO = self.dio.dtFuncDIO
            # Parameters for a device's DigitalIO instrument, these
            # are stored in IO object.
            self.iHnd = iHnd
            self.retOutputEnableMask = c_uint(0)
            self.uiOutputEnable = c_uint(0)
            self.retOutputEnable = c_uint(0)
            self.retOutputMask = c_uint(0)
            self.uiOutput = c_uint(0)
            self.retOutput = c_uint(0)
            self.retUp, self.retDown = c_uint(0), c_uint(0)
            self.uiUp, self.uiDown = c_uint(0), c_uint(0)
            self.channel = c_int(0)
            self.retAmpMin, self.retAmpMax = c_double(0.0), c_double(0.0)
            self.retAmpSteps, self.retSlewSteps = c_uint(0), c_uint(0)
            self.amp, self.slew = c_double(0.0), c_uint(0)
            self.retAmp, self.retSlew = c_double(0.0), c_uint(0)
            self.retInputMask = c_uint(0)
            self.retInput = c_uint(0)
            self.retllOutputEnableMask = c_ulonglong(0)
            self.llOutputEnable = c_ulonglong(0)
            self.retllOutputEnable = c_ulonglong(0)
            self.retllOutputMask = c_ulonglong(0)
            self.llOutput = c_ulonglong(0)
            self.retllOutput = c_ulonglong(0)
            self.retllInputMask = c_ulonglong(0)
            self.retllInput = c_ulonglong(0)
            # Dicts to be used in IO(), OutEnable(), Pull(), Drive() and Input()
            # member functions.
            self.auxIO = { "Reset" : False, "Configure" : False, "Status" : False }
            self.auxOutput = { "OutputEnableInfo" : False, "OutputEnable" : False,
                               "OutputInfo" : False, "Output" : False, "OutputEnableInfo64" : False,
                               "OutputEnable64" : False, "OutputInfo64" : False, "Output64" : False
                               }
            self.auxPull = { "Info" : False }
            self.auxDrive = { "Info" : False }
            self.auxInput = { "Info" : False, "Status" : False, "Info64" : False,
                              "Status64" : False
                              }

        def WpDwfDigitalIOReset(self,
                                hdwf : c_int
                                ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalIOConfigure(self,
                                    hdwf : c_int
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOConfigure
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalIOStatus(self,
                                 hdwf : c_int
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOStatus
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalIOOutputEnableInfo(self,
                                           hdwf : c_int,
                                           pfsOutputEnableMask : POINTER(c_uint)
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsOutputEnableMask) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableInfo
                          )(hdwf, pfsOutputEnableMask)
                return iretVal
            return WpFnGeneric(hdwf, pfsOutputEnableMask)

        def WpDwfDigitalIOOutputEnableSet(self,
                                          hdwf : c_int,
                                          fsOutputEnable : c_uint
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint)
            def WpFnGeneric(hdwf, fsOutputEnable) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableSet
                          )(hdwf, fsOutputEnable)
                return iretVal
            return WpFnGeneric(hdwf, fsOutputEnable)

        def WpDwfDigitalIOOutputEnableGet(self,
                                          hdwf : c_int,
                                          pfsOutputEnable : POINTER(c_uint)
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsOutputEnable) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableGet
                          )(hdwf, pfsOutputEnable)
                return iretVal
            return WpFnGeneric(hdwf, pfsOutputEnable)

        def WpDwfDigitalIOOutputInfo(self,
                                     hdwf : c_int,
                                     pfsOutputMask : POINTER(c_uint)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsOutputMask) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputInfo
                          )(hdwf, pfsOutputMask)
                return iretVal
            return WpFnGeneric(hdwf, pfsOutputMask)

        def WpDwfDigitalIOOutputSet(self,
                                    hdwf : c_int,
                                    fsOutput : c_uint
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint)
            def WpFnGeneric(hdwf, fsOutput) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputSet
                          )(hdwf, fsOutput)
                return iretVal
            return WpFnGeneric(hdwf, fsOutput)

        def WpDwfDigitalIOOutputGet(self,
                                    hdwf : c_int,
                                    pfsOutput : POINTER(c_uint)
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsOutput) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputGet
                          )(hdwf, pfsOutput)
                return iretVal
            return WpFnGeneric(hdwf, pfsOutput)

        def WpDwfDigitalIOPullInfo(self,
                                   hdwf : c_int,
                                   pfsUp : c_uint,
                                   pfsDown : c_uint
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint,
                       c_uint)
            def WpFnGeneric(hdwf, pfsUp, pfsDown) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOPullInfo
                          )(hdwf, pfsUp, pfsDown)
                return iretVal
            return WpFnGeneric(hdwf, pfsUp, pfsDown)

        def WpDwfDigitalIOPullSet(self,
                                  hdwf : c_int,
                                  fsUp : c_uint,
                                  fsDown : c_uint
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint,
                       c_uint)
            def WpFnGeneric(hdwf, fsUp, fsDown) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOPullSet
                          )(hdwf, fsUp, fsDown)
                return iretVal
            return WpFnGeneric(hdwf, fsUp, fsDown)

        def WpDwfDigitalIOPullGet(self,
                                  hdwf : c_int,
                                  pfsUp : POINTER(c_uint),
                                  pfsDown : POINTER(c_uint)
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint),
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsUp, pfsDown) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOPullGet
                          )(hdwf, pfsUp, pfsDown)
                return iretVal
            return WpFnGeneric(hdwf, pfsUp, pfsDown)

        def WpDwfDigitalIODriveInfo(self,
                                    hdwf : c_int,
                                    channel : c_int,
                                    ampMin : POINTER(c_double),
                                    ampMax : POINTER(c_double),
                                    ampSteps : POINTER(c_uint),
                                    slewSteps : POINTER(c_uint)
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_double), POINTER(c_double), POINTER(c_uint),
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, channel, ampMin,
                            ampMax, ampSteps, slewSteps) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIODriveInfo
                          )(hdwf, channel, ampMin,
                            ampMax, ampSteps, slewSteps)
                return iretVal
            return WpFnGeneric(hdwf, channel, ampMin,
                               ampMax, ampSteps, slewSteps)

        def WpDwfDigitalIODriveSet(self,
                                   hdwf : c_int,
                                   channel : c_int,
                                   amp : c_double,
                                   slew : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_double, c_int)
            def WpFnGeneric(hdwf, channel, amp,
                            slew) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIODriveSet
                          )(hdwf, channel, c_double(amp),
                            slew)
                return iretVal
            return WpFnGeneric(hdwf, channel, amp,
                               slew)

        def WpDwfDigitalIODriveGet(self,
                                   hdwf : c_int,
                                   channel : c_int,
                                   pamp : POINTER(c_double),
                                   pslew : POINTER(c_int)
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_double), POINTER(c_int))
            def WpFnGeneric(hdwf, channel, pamp, pslew) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDwfDigitalIODriveGet
                          )(hdwf, channel, pamp, pslew)
                return iretVal
            return WpFnGeneric(hdwf, channel, pamp, pslew)

        def WpDwfDigitalIOInputInfo(self,
                                    hdwf : c_int,
                                    pfsInputMask : POINTER(c_uint)
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsInputMask) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOInputInfo
                          )(hdwf, pfsInputMask)
                return iretVal
            return WpFnGeneric(hdwf, pfsInputMask)

        def WpDwfDigitalIOInputStatus(self,
                                      hdwf : c_int,
                                      pfsInput : POINTER(c_uint)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsInput) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDwfDigitalIOInputStatus
                          )(hdwf, pfsInput)
                return iretVal
            return WpFnGeneric(hdwf, pfsInput)

        def WpDwfDigitalIOOutputEnableInfo64(self,
                                             hdwf : c_int,
                                             pfsOutputEnableMask : POINTER(c_ulonglong)
                                             ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ulonglong))
            def WpFnGeneric(hdwf, pfsOutputEnableMask) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableInfo64
                          )(hdwf, pfsOutputEnableMask)
                return iretVal
            return WpFnGeneric(hdwf, pfsOutputEnableMask)

        def WpDwfDigitalIOOutputEnableSet64(self,
                                            hdwf : c_int,
                                            fsOutputEnable : c_ulonglong
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_ulonglong)
            def WpFnGeneric(hdwf, fsOutputEnable) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableSet64
                          )(hdwf, fsOutputEnable)
                return iretVal
            return WpFnGeneric(hdwf, fsOutputEnable)

        def WpDwfDigitalIOOutputEnableGet64(self,
                                            hdwf : c_int,
                                            pfsOutputEnable : POINTER(c_ulonglong)
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ulonglong))
            def WpFnGeneric(hdwf, pfsOutputEnable) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputEnableGet64
                          )(hdwf, pfsOutputEnable)
                return iretVal
            return WpFnGeneric(hdwf, pfsOutputEnable)

        def WpDwfDigitalIOOutputInfo64(self,
                                       hdwf : c_int,
                                       pfsOutputMask : POINTER(c_ulonglong)
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, POINTER(c_ulonglong))
            def WpFnGeneric(hdwf, pfsOutputMask) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputInfo64
                          )(hdwf, pfsOutputMask)
                return iretVal
            return WpFnGeneric(hdwf, pfsOutputMask)

        def WpDwfDigitalIOOutputSet64(self,
                                      hdwf : c_int,
                                      fsOutput : c_ulonglong
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ulonglong)
            def WpFnGeneric(hdwf, fsOutput) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputSet64
                          )(hdwf, fsOutput)
                return iretVal
            return WpFnGeneric(hdwf, fsOutput)

        def WpDwfDigitalIOOutputGet64(self,
                                      hdwf : c_int,
                                      pfsOutput : POINTER(c_ulonglong)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ulonglong))
            def WpFnGeneric(hdwf, pfsOutput) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOOutputGet64
                          )(hdwf, pfsOutput)
                return iretVal
            return WpFnGeneric(hdwf, pfsOutput)

        def WpDwfDigitalIOInputInfo64(self,
                                      hdwf : c_int,
                                      pfsInputMask : POINTER(c_ulonglong)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ulonglong))
            def WpFnGeneric(hdwf, pfsInputMask) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOInputInfo64
                          )(hdwf, pfsInputMask)
                return iretVal
            return WpFnGeneric(hdwf, pfsInputMask)

        def WpDwfDigitalIOInputStatus64(self,
                                        hdwf : c_int,
                                        pfsInput : POINTER(c_ulonglong)
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ulonglong))
            def WpFnGeneric(hdwf, pfsInput) -> int:
                iretVal = self.dtFuncDIO.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalIOInputStatus64
                          )(hdwf, pfsInput)
                return iretVal
            return WpFnGeneric(hdwf, pfsInput)

        def cntrlDigitalIO(self,
                           dIO : dict
                           ) -> int:
            """
            @Description
            @Parameters
            dIO : Dictionary only for enable flags.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            None
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dIO.keys())
            if not ("Reset" in lsKeys or
                    "Configure" in lsKeys or
                    "Status" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dIO["Reset"]:
                iRet = self.WpDwfDigitalIOReset(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dIO["Configure"]:
                iRet = self.WpDwfDigitalIOConfigure(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dIO["Status"]:
                iRet = self.WpDwfDigitalIOStatus(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalIOOutput(self,
                                 dOutEnable : dict,
                                 bSet : bool,
                                 bGet : bool
                                 ) -> int:
            """
            @Description
            Control IO output and retrive its data like enable info on 32b
            or 64b, all functions are categorized into 4 sections with their
            independent conditions. These categories are OutputEnable(Info),
            Output(Info), OutputEnable(Info){64}, Output(Info){64}.
            @Parameters
            dOutEnable : Dictionary only for output enable flags.
            bSet : Flag for pull setter.
            bGet : Flag for pull getter.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            None
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dOutEnable.keys())
            if not ("OutputEnableInfo" in lsKeys or
                    "OutputEnable" in lsKeys or
                    "OutputInfo" in lsKeys or
                    "Output" in lsKeys or
                    "OutputEnableInfo64" in lsKeys or
                    "OutputEnable64" in lsKeys or
                    "OutputInfo64" in lsKeys or
                    "Output64" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dOutEnable["OutputEnableInfo"]:
                iRet = self.WpDwfDigitalIOOutputEnableInfo(
                            self.iHnd,
                            self.retOutputEnableMask
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dOutEnable["OutputEnableInfo"] = False
            
            if dOutEnable["OutputEnable"] and bSet:
                if bSet:
                    iRet = self.WpDwfDigitalIOOutputEnableSet(
                                self.iHnd,
                                self.uiOutputEnable
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalIOOutputEnableGet(
                                self.iHnd,
                                self.retOutputEnable
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dOutEnable["OutputEnable"] = False
            
            if dOutEnable["OutputInfo"]:
                iRet = self.WpDwfDigitalIOOutputInfo(
                            self.iHnd,
                            self.retOutputMask
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dOutEnable["OutputInfo"] = False
            
            if dOutEnable["Output"] and bSet:
                if bSet:
                    iRet = self.WpDwfDigitalIOOutputSet(
                                self.iHnd,
                                self.uiOutput
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalIOOutputGet(
                                self.iHnd,
                                self.retOutput
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dOutEnable["Output"] = False
            
            if dOutEnable["OutputEnableInfo64"]:
                iRet = self.WpDwfDigitalIOOutputEnableInfo64(
                            self.iHnd,
                            self.retllOutputMask
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dOutEnable["OutputEnableInfo64"] = False
            
            if dOutEnable["OutputEnable64"] and bSet:
                if bSet:
                    iRet = self.WpDwfDigitalIOOutputEnableSet64(
                                self.iHnd,
                                self.llOutputEnable
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalIOOutputEnableGet64(
                                self.iHnd,
                                self.retllOutputEnable
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dOutEnable["OutputEnable64"] = False
            
            if dOutEnable["OutputInfo64"]:
                iRet = self.WpDwfDigitalIOOutputInfo64(
                            self.iHnd,
                            self.retllOutputMask
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dOutEnable["OutputInfo64"] = False
            
            if dOutEnable["Output64"]:
                if bSet:
                    iRet = self.WpDwfDigitalIOOutputSet64(
                                self.iHnd,
                                self.llOutput
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalIOOutputGet64(
                                self.iHnd,
                                self.retllOutput
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dOutEnable["Output64"] = False
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalIOPull(self,
                               dPull : dict,
                               bSet : bool,
                               bGet : bool
                               ) -> int:
            """
            @Description
            Get or set pull type (Up/Down) for an individual DIO pin, these
            attributes are self contained into IO object, so setting them
            will be used here. This approach leads to a much better
            versatility for manipulating more devices.
            @Parameters
            dPull : Dictionary only for pull info flag.
            bSet : Flag for pull setter.
            bGet : Flag for pull getter.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            None
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dPull.keys())
            if not ("Info" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dPull["Info"]:
                iRet = self.WpDwfDigitalIOPullInfo(
                            self.iHnd,
                            self.retUp,
                            self.retDown
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dPull["Info"] = False
            
            if bSet:
                iRet = self.WpDwfDigitalIOPullSet(
                            self.iHnd,
                            self.uiUp,
                            self.uiDown
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalIOPullGet(
                            self.iHnd,
                            self.retUp,
                            self.retDown
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalIODrive(self,
                                dDrive : dict,
                                bSet : bool,
                                ) -> int:
            """
            @Description
            Get or set drive strenght for an individual DIO pin, these
            attributes are self contained into IO object, so setting them
            will be used here. This approach leads to a much better
            versatility for manipulating more devices.
            @Parameters
            dDrive : Dictionary only for drive info flag.
            bSet : Flag for drive setter.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            None
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dDrive.keys())
            if not ("Info" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dDrive["Info"]:
                iRet = self.WpDwfDigitalIODriveInfo(
                            self.iHnd,
                            self.channel,
                            self.retAmpMin,
                            self.retAmpMax,
                            self.retAmpSteps,
                            self.retSlewSteps
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dDrive["Info"] = False
            
            if bSet:
                iRet = self.WpDwfDigitalIODriveSet(
                            self.iHnd,
                            self.channel,
                            self.amp,
                            self.slew
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalIOInput(self,
                                dInput : dict,
                                ) -> int:
            """
            @Description
            Request info/status from a specific board for DigitalIO
            instrument, input mask or simply input w.r to DIO header
            on board. These can be 32b or 64b format.
            @Parameters
            dInput : Dictionary holding values of True/False (bool type)
                     that represent which type of IOInput is requested to
                     retrive Input(Mask) with 32/64 bit. These can be checked
                     with their getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            None
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dInput.keys())
            if not ("Info" in lsKeys or
                    "Status" in lsKeys or
                    "Info64" in lsKeys or
                    "Status64" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dInput["Info"]:
                iRet = self.WpDwfDigitalIOInputInfo(
                            self.iHnd,
                            self.retInputMask
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dInput["Info"] = False
            
            if dInput["Status"]:
                iRet = self.WpDwfDigitalIOInputStatus(
                            self.iHnd,
                            self.retInput
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dInput["Status"] = False
            
            if dInput["Info64"]:
                iRet = self.WpDwfDigitalIOInputInfo64(
                            self.iHnd,
                            self.retllInputMask
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dInput["Info64"] = False
            
            if dInput["Status64"]:
                iRet = self.WpDwfDigitalIOInputStatus64(
                            self.iHnd,
                            self.retllInput
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dInput["Status64"] = False
            
            return DigitalInstruments.SUCCESS

        def Io(self,
               bReset=False,
               bStatus=False,
               bEnable=False,
               bInfo=False,
               format=32,
               dDio={"DIO0":0,"DIO1":0,"DIO2":0,"DIO3":0,
                     "DIO4":0,"DIO5":0,"DIO6":0,"DIO7":0,
                     "DIO8":0,"DIO9":0,"DIO10":0,"DIO11":0,
                     "DIO12":0,"DIO13":0,"DIO14":0,"DIO15":0
                     },
               dOutput={"Mask":0,"DIO":-1,"iDIO":-1
                        },
               dPull={"PullUp":0,"PullDown":0,
                      "iPullUp":0,"iPullDown":0,
                      "MaskPullUp":0,"MaskPullDown":0
                      },
               dDrive={"Channel":0,"Amplitude":0.0,"Slew":0,
                       "iAmplitude":0.0,"iSlew":0,"AmpMin":0.0,
                       "AmpMax":0.0,"AmpSteps":0,"SlewSteps":0
                       },
               dInput={"stsMask":0,"Mask":0
                       }
               ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            i ~ prefix := input parameter, one of the functions below
            will change it.
            """
            try:
                iRet = 0
                if not (bReset and bStatus):
                    self.auxIO["Configure"] = True
                    iRet = self.cntrlDigitalIO(dIO=self.auxIO)
                else:
                    if bReset:
                        self.auxIO["Reset"] = True
                        iRet = self.cntrlDigitalIO(dIO=self.auxIO)
                    elif bStatus:
                        self.auxIO["Status"] = True
                        iRet = self.cntrlDigitalIO(dIO=self.auxIO)
                    else:
                        raise ErrorWpFnGenericInstrument("IO error: not started")
                if dOutput["DIO"] == -1:
                    lcMask = 0
                    for x in range(0, 16):
                        lcMask = lcMask | ((dDio["DIO" + str(x)] & 0x01) << x)
                    dOutput["DIO"] = lcMask
                self.Output(format=format, bEnable=bEnable, data=dOutput)
                self.Pull(data=dPull)
                self.Drive(data=dDrive)
                self.Input(format=format, bStatus=bStatus, bInfo=bInfo, data=dInput)
                
            except ErrorWpFnGenericInstrument as err:
                print(err)

        def Output(self,
                   format=32, # 32,64
                   bEnable=False,
                   data={"Mask":0,"DIO":-1,"iDIO":-1}
                   ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            i ~ prefix := input parameter, one of the functions below
            will change it.
            """
            try:
                # 32b or 64b
                if format == 32:
                    if bEnable:
                        self.auxOutput["OutputEnableInfo"] = True
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=False,
                                    bGet=False
                                    )
                        data["Mask"] = self.retOutputEnableMask.value
                        self.auxOutput["OutputEnable"] = True
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=False,
                                    bGet=True
                                    )
                        data["iDIO"] = self.retOutputEnable.value
                        self.auxOutput["OutputEnable"] = True
                        self.uiOutputEnable = c_uint(data["DIO"])
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=True,
                                    bGet=False
                                    )
                    else:
                        self.auxOutput["OutputInfo"] = True
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=False,
                                    bGet=False
                                    )
                        data["Mask"] = self.retOutputMask.value
                        self.auxOutput["Output"] = True
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=False,
                                    bGet=True
                                    )
                        data["iDIO"] = self.retOutput.value
                        self.auxOutput["Output"] = True
                        self.uiOutput = c_uint(data["DIO"])
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=True,
                                    bGet=False
                                    )
                
                elif format == 64:
                    if bEnable:
                        self.auxOutput["OutputEnableInfo64"] = True
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=False,
                                    bGet=False
                                    )
                        data["Mask"] = self.retllOutputEnableMask.value
                        self.auxOutput["OutputEnable64"] = True
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=False,
                                    bGet=True
                                    )
                        data["iDIO"] = self.retllOutputEnable.value
                        self.auxOutput["OutputEnable64"] = True
                        self.llOutputEnable = c_ulonglong(data["DIO"])
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=True,
                                    bGet=False
                                    )
                    else:
                        self.auxOutput["OutputInfo64"] = True
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=False,
                                    bGet=False
                                    )
                        data["Mask"] = self.retllOutputMask.value
                        self.auxOutput["Output64"] = True
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=False,
                                    bGet=True
                                    )
                        data["iDIO"] = self.retllOutput.value
                        self.auxOutput["Output64"] = True
                        self.llOutput = c_ulonglong(data["DIO"])
                        iRet = self.cntrlDigitalIOOutput(
                                    dOutEnable=self.auxOutput,
                                    bSet=True,
                                    bGet=False
                                    )
                else:
                    raise ErrorWpFnGenericInstrument("Output error: wrong format")
                
            except ErrorWpFnGenericInstrument as err:
                print(err)

        def Pull(self,
                 data={"PullUp":0,"PullDown":0,
                       "iPullUp":0,"iPullDown":0,
                       "MaskPullUp":0,"MaskPullDown":0}
                 ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            i ~ prefix := input parameter, one of the functions below
            will change it.
            """
            try:
                self.auxPull["Info"] = True
                iRet = self.cntrlDigitalIOPull(dPull=self.auxPull, bSet=False, bGet=False)
                data["MaskPullUp"] = self.retUp.value
                data["MaskPullDown"] = self.retDown.value
                iRet = self.cntrlDigitalIOPull(dPull={}, bSet=False, bGet=True)
                data["iPullUp"] = self.retUp.value
                data["iPullDown"] = self.retDown.value
                self.uiUp = c_uint(data["PullUp"])
                self.uiDown = c_uint(data["PullDown"])
                iRet = self.cntrlDigitalIOPull(dPull={}, bSet=True, bGet=False)
                
            except ErrorWpFnGenericInstrument as err:
                print(err)

        def Drive(self,
                  data={"Channel":0,"Amplitude":0.0,"Slew":0,
                        "iAmplitude":0.0,"iSlew":0,"AmpMin":0.0,
                        "AmpMax":0.0,"AmpSteps":0,"SlewSteps":0}
                  ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            i ~ prefix := input parameter, one of the functions below
            will change it.
            """
            try:
                self.auxDrive["Info"] = True
                self.channel = c_int(data["Channel"])
                iRet = self.cntrlDigitalIODrive(dDrive=self.auxDrive, bSet=False)
                data["AmpMin"] = self.retAmpMin.value
                data["AmpMax"] = self.retAmpMax.value
                data["AmpSteps"] = self.retAmpSteps.value
                data["SlewSteps"] = self.retSlewSteps.value
                iRet = self.cntrlDigitalIODrive(dDrive={}, bSet=False)
                data["iAmplitude"] = self.retAmp.value
                data["iSlew"] = self.retSlew.value
                self.amp = c_double(data["Amplitude"])
                self.slew = c_uint(data["Slew"])
                iRet = self.cntrlDigitalIODrive(dDrive={}, bSet=True)
                
            except ErrorWpFnGenericInstrument as err:
                print(err)

        def Input(self,
                  format=32, # 32,64
                  bStatus=False,
                  bInfo=False,
                  data={"stsMask":0,"Mask":0}
                  ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            """
            try:
                iRet = 0
                if bInfo:
                    self.auxInput["Info"] = True
                # 32b or 64b
                if format == 32:
                    if bInfo:
                        iRet = self.cntrlDigitalIOInput(dInput=self.auxInput, bGet=False)
                        data["Mask"] = self.retInputMask.value
                    elif bStatus:
                        iRet = self.cntrlDigitalIOInput(dInput=self.auxInput, bGet=True)
                        data["stsMask"] = self.retInput.value
                elif format == 64:
                    if bInfo:
                        iRet = self.cntrlDigitalIOInput(dInput=self.auxInput, bGet=False)
                        data["Mask"] = self.retllInputMask.value
                    elif bStatus:
                        iRet = self.cntrlDigitalIOInput(dInput=self.auxInput, bGet=True)
                        data["stsMask"] = self.retllInput.value
                else:
                    raise ErrorWpFnGenericInstrument("Input error: wrong format")
                
            except ErrorWpFnGenericInstrument as err:
                print(err)

    class LogicAnalyzerConfig:
        """
        Digital Logic Analyzer resources for a single device are encapsulated
        here which can be used for more than one device. Its handler
        is stored then an LogicAnalyzerConfig instance is created, so the functions
        that are intended to be used are cntrlDigitalInStatus,
        cntrlDigitalInCounter, cntrlDigitalInClock and cntrlDigitalInDivider,
        cntrlDigitalInSample, cntrlDigitalInBuffer, cntrlDigitalInAcquisition,
        cntrlDigitalInTrigger, these use the wrapper functions that starts with WpDwf... .
        @Notes
        Functions with the prefix WpDwf... can be used, but they are
        only encapsulating ctypes library, which is of use for
        waveforms' runtime library, to use python built-in types and
        build setups independently of waveforms application.
        """
        def __init__(self,
                     iHnd : c_int
                     ):
            self.la = LogicAnalyzer()
            self.dtFuncLA = self.la.dtFuncLA
            # Parameters for a device's DigitalIn instrument, these
            # are stored in LogicAnalyzerConfig object.
            self.iHnd = iHnd
            self.iReconfigure, self.iStart = c_int(0), c_int(0)
            self.iReadData, self.retSts = c_int(0), c_int(0)
            self.retSamplesLeft = c_int(0)
            self.retSamplesValid = c_int(0)
            self.retIdxWrite = c_int(0)
            self.retAuto = c_int(0)
            self.rgData, self.iCountOfBytes = (c_uint*1)(), c_int(0)
            self.iIdxSample, = c_int(0)
            self.iBitShift = c_int(0)
            self.cdDataAvailable, self.cdDataLost = c_int(0), c_int(0)
            self.cdDataCorrupt = c_int(0)
            self.retUiSecUtc, self.retUiTick, = c_uint(0), c_uint(0)
            self.retUiTicksPerSecond = c_uint(0)
            self.retCntMax, self.retSecMax = c_double(0.0), c_double(0.0)
            self.sec = c_double(0.0)
            self.retSec = c_double(0.0)
            self.retCnt, self.retFreq, self.retTick = c_int(0), c_int(0), c_int(0)
            self.retHzFreq = c_double(0.0)
            self.retFsDwfDigitalInClockSource = c_double(0.0)
            self.uiClockSource, self.retUiClockSource = c_uint(0), c_uint(0)
            self.retDivMax = c_uint(0)
            self.div = c_uint(0)
            self.retDiv = c_uint(0)
            self.retNBits = c_int(0)
            self.nBits = c_int(0)
            self.iDioFirst = c_int(0)
            self.retNSizeMax = c_int(0)
            self.iSize, self.retNSize = c_int(0), c_int(0)
            self.retMax, self.iN, self.retIN = c_int(0), c_int(0), c_int(0)
            self.retFsDwfDigitalInSampleMode = c_int(0)
            self.inSampleMode, self.retInSampleMode = c_int(0), c_int(0)
            self.uiFs, self.retUiFs = c_uint(0), c_uint(0)
            self.retiFsacqmode = c_int(0)
            self.acqmode, self.retAcqmode = c_int(0), c_int(0)
            self.trigsrc, self.retTrigsrc = c_int(0), c_int(0)
            self.slope, self.retSlope = c_int(0), c_int(0)
            self.retNSamplesAfterTriggerMax = c_uint(0)
            self.cSamplesAfterTrigger = c_uint(0)
            self.retCSamplesAfterTrigger = c_uint(0)
            self.cSamplesBeforeTrigger = c_uint(0)
            self.retCSamplesBeforeTrigger = c_uint(0)
            self.retSecMin, self.retSecMax = c_double(0.0), c_double(0.0)
            self.retNSteps = c_double(0.0)
            self.secTimeout, self.retSecTimeout = c_double(0.0), c_double(0.0)
            self.retFsLevelLow, self.retFsLevelHigh = c_uint(0), c_uint(0)
            self.retFsEdgeRise = c_uint(0)
            self.retFsEdgeFall = c_uint(0)
            self.FsLevelLow, self.FsLevelHigh = c_uint(0), c_uint(0)
            self.FsEdgeRise = c_uint(0)
            self.FsEdgeFall = c_uint(0)
            self.retllFsLevelLow, self.retllFsLevelHigh = c_ulonglong(0), c_ulonglong(0)
            self.retllFsEdgeRise = c_ulonglong(0)
            self.retllFsEdgeFall = c_ulonglong(0)
            self.llFsLevelLow, self.llFsLevelHigh = c_ulonglong(0), c_ulonglong(0)
            self.llFsEdgeRise = c_ulonglong(0)
            self.llFsEdgeFall = c_ulonglong(0)
            self.cCount, self.fRestart = c_int(0), c_int(0)
            self.secMin, self.secMax = c_double(0.0), c_double(0.0)
            self.idxSync = c_int(0)
            self.iPin, self.fsMask = c_int(0), c_uint(0)
            self.fsValue, self.cBitStuffing = c_uint(0), c_int(0)

        def WpDwfDigitalInReset(self,
                                hdwf : c_int
                                ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalInConfigure(self,
                                    hdwf : c_int,
                                    fReconfigure : c_int,
                                    fStart : c_int
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fReconfigure, fStart) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInConfigure
                          )(hdwf, fReconfigure, fStart)
                return iretVal
            return WpFnGeneric(hdwf, fReconfigure, fStart)

        def WpDwfDigitalInStatus(self,
                                 hdwf : c_int,
                                 fReadData : c_int,
                                 psts : POINTER(c_ubyte)
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_ubyte))
            def WpFnGeneric(hdwf, fReadData, psts) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutStatus
                          )(hdwf, fReadData, psts)
                return iretVal
            return WpFnGeneric(hdwf, fReadData, psts)

        def WpDwfDigitalInStatusSamplesLeft(self,
                                            hdwf : c_int,
                                            pcSamplesLeft : POINTER(c_int)
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pcSamplesLeft) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusSamplesLeft
                          )(hdwf, pcSamplesLeft)
                return iretVal
            return WpFnGeneric(hdwf, pcSamplesLeft)

        def WpDwfDigitalInStatusSamplesValid(self,
                                             hdwf : c_int,
                                             pcSamplesValid : POINTER(c_int)
                                             ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pcSamplesValid) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusSamplesValid
                          )(hdwf, pcSamplesValid)
                return iretVal
            return WpFnGeneric(hdwf, pcSamplesValid)

        def WpDwfDigitalInStatusIndexWrite(self,
                                           hdwf : c_int,
                                           pidxWrite : POINTER(c_int)
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pidxWrite) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusIndexWrite
                          )(hdwf, pidxWrite)
                return iretVal
            return WpFnGeneric(hdwf, pidxWrite)

        def WpDwfDigitalInStatusAutoTriggered(self,
                                              hdwf : c_int,
                                              pfAuto : POINTER(c_int)
                                              ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfAuto) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusAutoTriggered
                          )(hdwf, pfAuto)
                return iretVal
            return WpFnGeneric(hdwf, pfAuto)

        def WpDwfDigitalInStatusData(self,
                                     hdwf : c_int,
                                     rgData : POINTER(c_void_p),
                                     countOfDataBytes : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_void_p),
                       c_int)
            def WpFnGeneric(hdwf, rgData, countOfDataBytes) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusData
                          )(hdwf, rgData, countOfDataBytes)
                return iretVal
            return WpFnGeneric(hdwf, rgData, countOfDataBytes)

        def WpDwfDigitalInStatusData2(self,
                                      hdwf : c_int,
                                      rgData : POINTER(c_void_p),
                                      idxSample : c_int,
                                      countOfDataBytes : c_int
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_void_p),
                       c_int, c_int)
            def WpFnGeneric(hdwf, rgData, idxSample,
                            countOfDataBytes) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusData2
                          )(hdwf, rgData, idxSample,
                            countOfDataBytes)
                return iretVal
            return WpFnGeneric(hdwf, rgData, idxSample,
                               countOfDataBytes)

        def WpDwfDigitalInStatusData3(self,
                                      hdwf : c_int,
                                      rgData : POINTER(c_void_p),
                                      idxSample : c_int,
                                      countOfDataBytes : c_int,
                                      bitShift : c_int
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_void_p),
                       c_int, c_int, c_int)
            def WpFnGeneric(hdwf, rgData, idxSample,
                            countOfDataBytes, bitShift) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusData3
                          )(hdwf, rgData, idxSample,
                            countOfDataBytes, bitShift)
                return iretVal
            return WpFnGeneric(hdwf, rgData, idxSample,
                               countOfDataBytes, bitShift)

        def WpDwfDigitalInStatusNoise2(self,
                                       hdwf : c_int,
                                       rgData : POINTER(c_void_p),
                                       idxSample : c_int,
                                       countOfDataBytes : c_int
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, rgData, idxSample,
                       countOfDataBytes)
            def WpFnGeneric(hdwf, rgData, idxSample,
                            countOfDataBytes) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusNoise2
                          )(hdwf, rgData, idxSample,
                            countOfDataBytes)
                return iretVal
            return WpFnGeneric(hdwf, rgData, idxSample,
                               countOfDataBytes)

        def WpDwfDigitalInStatusNoise3(self,
                                       hdwf : c_int,
                                       rgData : POINTER(c_void_p),
                                       idxSample : c_int,
                                       countOfDataBytes : c_int,
                                       bitShift : c_int
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, POINTER(c_void_p), c_int,
                       c_int, c_int)
            def WpFnGeneric(hdwf, rgData, idxSample,
                            countOfDataBytes, bitShift) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusNoise3
                          )(hdwf, rgData, idxSample,
                            countOfDataBytes, bitShift)
                return iretVal
            return WpFnGeneric(hdwf, rgData, idxSample,
                               countOfDataBytes, bitShift)

        def WpDwfDigitalInStatusRecord(self,
                                       hdwf : c_int,
                                       pcdDataAvailable : POINTER(c_int),
                                       pcdDataLost : POINTER(c_int),
                                       pcdDataCorrupt : POINTER(c_int)
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int),
                       POINTER(c_int), POINTER(c_int))
            def WpFnGeneric(hdwf, pcdDataAvailable, pcdDataLost,
                            pcdDataCorrupt) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusRecord
                          )(hdwf, pcdDataAvailable, pcdDataLost,
                            pcdDataCorrupt)
                return iretVal
            return WpFnGeneric(hdwf, pcdDataAvailable, pcdDataLost,
                               pcdDataCorrupt)

        def WpDwfDigitalInStatusCompress(self,
                                         hdwf : c_int,
                                         pcdDataAvailable : POINTER(c_int),
                                         pcdDataLost : POINTER(c_int),
                                         pcdDataCorrupt : POINTER(c_int)
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int),
                       POINTER(c_int), POINTER(c_int))
            def WpFnGeneric(hdwf, pcdDataAvailable, pcdDataLost,
                            pcdDataCorrupt) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusCompress
                          )(hdwf, pcdDataAvailable, pcdDataLost,
                            pcdDataCorrupt)
                return iretVal
            return WpFnGeneric(hdwf, pcdDataAvailable, pcdDataLost,
                               pcdDataCorrupt)

        def WpDwfDigitalInStatusCompressed(self,
                                           hdwf : c_int,
                                           rgData : POINTER(c_void_p),
                                           countOfBytes : c_int
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_void_p))
            def WpFnGeneric(hdwf, rgData, countOfBytes) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusCompressed
                          )(hdwf, rgData, countOfBytes)
                return iretVal
            return WpFnGeneric(hdwf, rgData, countOfBytes)

        def WpDwfDigitalInStatusCompressed2(self,
                                            hdwf : c_int,
                                            rgData : POINTER(c_void_p),
                                            idxSample : c_int,
                                            countOfBytes : c_int
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, rgData, idxSample,
                       countOfBytes)
            def WpFnGeneric(hdwf, rgData, idxSample,
                            countOfBytes) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusCompressed2
                          )(hdwf, rgData, idxSample,
                            countOfBytes)
                return iretVal
            return WpFnGeneric(hdwf, rgData, idxSample,
                               countOfBytes)

        def WpDwfDigitalInStatusTime(self,
                                     hdwf : c_int,
                                     psecUtc : POINTER(c_uint),
                                     ptick : POINTER(c_uint),
                                     pticksPerSecond : POINTER(c_uint)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint),
                       POINTER(c_uint), POINTER(c_uint))
            def WpFnGeneric(hdwf, psecUtc, ptick,
                            pticksPerSecond) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInStatusTime
                          )(hdwf, psecUtc, ptick,
                            pticksPerSecond)
                return iretVal
            return WpFnGeneric(hdwf, psecUtc, ptick,
                               pticksPerSecond)

        def WpDwfDigitalInCounterInfo(self,
                                      hdwf : c_int,
                                      pcntMax : POINTER(c_double),
                                      psecMax : POINTER(c_double)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double),
                       POINTER(c_double))
            def WpFnGeneric(hdwf, pcntMax, psecMax) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInCounterInfo
                          )(hdwf, pcntMax, psecMax)
                return iretVal
            return WpFnGeneric(hdwf, pcntMax, psecMax)

        def WpDwfDigitalInCounterSet(self,
                                     hdwf : c_int,
                                     sec : c_double
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, sec) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInCounterSet
                          )(hdwf, c_double(sec))
                return iretVal
            return WpFnGeneric(hdwf, sec)

        def WpDwfDigitalInCounterGet(self,
                                     hdwf : c_int,
                                     psec : POINTER(c_double)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, psec) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInCounterGet
                          )(hdwf, psec)
                return iretVal
            return WpFnGeneric(hdwf, psec)

        def WpDwfDigitalInCounterStatus(self,
                                        hdwf : c_int,
                                        pcnt : POINTER(c_double),
                                        pfreq : POINTER(c_double),
                                        ptick : POINTER(c_int)
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double),
                       POINTER(c_double), POINTER(c_int))
            def WpFnGeneric(hdwf, pcnt, pfreq,
                            ptick) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInCounterStatus
                          )(hdwf, pcnt, pfreq,
                            ptick)
                return iretVal
            return WpFnGeneric(hdwf, pcnt, pfreq,
                               ptick)

        def WpDwfDigitalInInternalClockInfo(self,
                                            hdwf : c_int,
                                            phzFreq : POINTER(c_double)
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, phzFreq) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInInternalClockInfo
                          )(hdwf, phzFreq)
                return iretVal
            return WpFnGeneric(hdwf, phzFreq)

        def WpDwfDigitalInClockSourceInfo(self,
                                          hdwf : c_int,
                                          pfsDwfDigitalInClockSource : POINTER(c_int)
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfsDwfDigitalInClockSource) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInClockSourceInfo
                          )(hdwf, pfsDwfDigitalInClockSource)
                return iretVal
            return WpFnGeneric(hdwf, pfsDwfDigitalInClockSource)

        def WpDwfDigitalInClockSourceSet(self,
                                         hdwf : c_int,
                                         v : c_int
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, v) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInClockSourceSet
                          )(hdwf, v)
                return iretVal
            return WpFnGeneric(hdwf, v)

        def WpDwfDigitalInClockSourceGet(self,
                                         hdwf : c_int,
                                         pv : POINTER(c_int)
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pv) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInClockSourceGet
                          )(hdwf, pv)
                return iretVal
            return WpFnGeneric(hdwf, pv)

        def WpDwfDigitalInDividerInfo(self,
                                      hdwf : c_int,
                                      pdivMax : POINTER(c_uint)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pdivMax) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInDividerInfo
                          )(hdwf, pdivMax)
                return iretVal
            return WpFnGeneric(hdwf, pdivMax)

        def WpDwfDigitalInDividerSet(self,
                                     hdwf : c_int,
                                     div : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, div) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInDividerSet
                          )(hdwf, div)
                return iretVal
            return WpFnGeneric(hdwf, div)

        def WpDwfDigitalInDividerGet(self,
                                     hdwf : c_int,
                                     pdiv : POINTER(c_int)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pdiv) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInDividerGet
                          )(hdwf, pdiv)
                return iretVal
            return WpFnGeneric(hdwf, pdiv)

        def WpDwfDigitalInBitsInfo(self,
                                   hdwf : c_int,
                                   pnBits : POINTER(c_int)
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pnBits) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInBitsInfo
                          )(hdwf, pnBits)
                return iretVal
            return WpFnGeneric(hdwf, pnBits)

        def WpDwfDigitalInSampleFormatSet(self,
                                          hdwf : c_int,
                                          nBits : c_int
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, nBits) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInSampleFormatSet
                          )(hdwf, nBits)
                return iretVal
            return WpFnGeneric(hdwf, nBits)

        def WpDwfDigitalInSampleFormatGet(self,
                                          hdwf : c_int,
                                          pnBits : POINTER(c_int)
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pnBits) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInSampleFormatGet
                          )(hdwf, pnBits)
                return iretVal
            return WpFnGeneric(hdwf, pnBits)

        def WpDwfDigitalInInputOrderSet(self,
                                        hdwf : c_int,
                                        fDioFirst : c_int
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fDioFirst) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInInputOrderSet
                          )(hdwf, fDioFirst)
                return iretVal
            return WpFnGeneric(hdwf, fDioFirst)

        def WpDwfDigitalInBufferSizeInfo(self,
                                         hdwf : c_int,
                                         pnSizeMax : POINTER(c_int)
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pnSizeMax) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInBufferSizeInfo
                          )(hdwf, pnSizeMax)
                return iretVal
            return WpFnGeneric(hdwf, pnSizeMax)

        def WpDwfDigitalInBufferSizeSet(self,
                                        hdwf : c_int,
                                        nSize : c_int
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, nSize) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInBufferSizeSet
                          )(hdwf, nSize)
                return iretVal
            return WpFnGeneric(hdwf, nSize)

        def WpDwfDigitalInBufferSizeGet(self,
                                        hdwf : c_int,
                                        pnSize : POINTER(c_int)
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pnSize) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInBufferSizeGet
                          )(hdwf, pnSize)
                return iretVal
            return WpFnGeneric(hdwf, pnSize)

        def WpDwfDigitalInBuffersInfo(self,
                                      hdwf : c_int,
                                      pMax : POINTER(c_int)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pMax) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInBuffersInfo
                          )(hdwf, pMax)
                return iretVal
            return WpFnGeneric(hdwf, pMax)

        def WpDwfDigitalInBuffersSet(self,
                                     hdwf : c_int,
                                     n : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, n) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInBuffersSet
                          )(hdwf, n)
                return iretVal
            return WpFnGeneric(hdwf, n)

        def WpDwfDigitalInBuffersGet(self,
                                     hdwf : c_int,
                                     pn : POINTER(c_int)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pn) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInBuffersGet
                          )(hdwf, pn)
                return iretVal
            return WpFnGeneric(hdwf, pn)

        def WpDwfDigitalInBuffersStatus(self,
                                        hdwf : c_int,
                                        pn : POINTER(c_int)
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pn) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInBuffersStatus
                          )(hdwf, pn)
                return iretVal
            return WpFnGeneric(hdwf, pn)

        def WpDwfDigitalInSampleModeInfo(self,
                                         hdwf : c_int,
                                         pfsDwfDigitalInSampleMode : POINTER(c_int)
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfsDwfDigitalInSampleMode) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInSampleModeInfo
                          )(hdwf, pfsDwfDigitalInSampleMode)
                return iretVal
            return WpFnGeneric(hdwf, pfsDwfDigitalInSampleMode)

        def WpDwfDigitalInSampleModeSet(self,
                                        hdwf : c_int,
                                        v : c_int
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, v) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInSampleModeSet
                          )(hdwf, v)
                return iretVal
            return WpFnGeneric(hdwf, v)

        def WpDwfDigitalInSampleModeGet(self,
                                        hdwf : c_int,
                                        pv : POINTER(c_int)
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pv) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInSampleModeGet
                          )(hdwf, pv)
                return iretVal
            return WpFnGeneric(hdwf, pv)

        def WpDwfDigitalInSampleSensibleSet(self,
                                            hdwf : c_int,
                                            fs : c_uint
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint)
            def WpFnGeneric(hdwf, fs) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInSampleSensibleSet
                          )(hdwf, fs)
                return iretVal
            return WpFnGeneric(hdwf, fs)

        def WpDwfDigitalInSampleSensibleGet(self,
                                            hdwf : c_int,
                                            pfs : POINTER(c_uint)
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pfs) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInSampleSensibleGet
                          )(hdwf, pfs)
                return iretVal
            return WpFnGeneric(hdwf, pfs)

        def WpDwfDigitalInAcquisitionModeInfo(self,
                                              hdwf : c_int,
                                              pfsacqmode : POINTER(c_int)
                                              ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfsacqmode) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInAcquisitionModeInfo
                          )(hdwf, pfsacqmode)
                return iretVal
            return WpFnGeneric(hdwf, pfsacqmode)

        def WpDwfDigitalInAcquisitionModeSet(self,
                                             hdwf : c_int,
                                             acqmode : c_int
                                             ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, acqmode) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInAcquisitionModeSet
                          )(hdwf, acqmode)
                return iretVal
            return WpFnGeneric(hdwf, acqmode)

        def WpDwfDigitalInAcquisitionModeGet(self,
                                             hdwf : c_int,
                                             pacqmode : POINTER(c_int)
                                             ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pacqmode) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInAcquisitionModeGet
                          )(hdwf, pacqmode)
                return iretVal
            return WpFnGeneric(hdwf, pacqmode)

        def WpDwfDigitalInTriggerSourceSet(self,
                                           hdwf : c_int,
                                           trigsrc : c_ubyte
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ubyte)
            def WpFnGeneric(hdwf, trigsrc) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSourceSet
                          )(hdwf, trigsrc)
                return iretVal
            return WpFnGeneric(hdwf, trigsrc)

        def WpDwfDigitalInTriggerSourceGet(self,
                                           hdwf : c_int,
                                           ptrigsrc : POINTER(c_ubyte)
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ubyte))
            def WpFnGeneric(hdwf, ptrigsrc) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSourceGet
                          )(hdwf, ptrigsrc)
                return iretVal
            return WpFnGeneric(hdwf, ptrigsrc)

        def WpDwfDigitalInTriggerSlopeSet(self,
                                          hdwf : c_int,
                                          slope : c_int
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, slope) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSlopeSet
                          )(hdwf, slope)
                return iretVal
            return WpFnGeneric(hdwf, slope)

        def WpDwfDigitalInTriggerSlopeGet(self,
                                          hdwf : c_int,
                                          pslope : POINTER(c_int)
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pslope) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSlopeGet
                          )(hdwf, pslope)
                return iretVal
            return WpFnGeneric(hdwf, pslope)

        def WpDwfDigitalInTriggerPositionInfo(self,
                                              hdwf : c_int,
                                              pnSamplesAfterTriggerMax : POINTER(c_uint)
                                              ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pnSamplesAfterTriggerMax) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPositionInfo
                          )(hdwf, pnSamplesAfterTriggerMax)
                return iretVal
            return WpFnGeneric(hdwf, pnSamplesAfterTriggerMax)

        def WpDwfDigitalInTriggerPositionSet(self,
                                             hdwf : c_int,
                                             cSamplesAfterTrigger : c_uint
                                             ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint)
            def WpFnGeneric(hdwf, cSamplesAfterTrigger) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPositionSet
                          )(hdwf, cSamplesAfterTrigger)
                return iretVal
            return WpFnGeneric(hdwf, cSamplesAfterTrigger)

        def WpDwfDigitalInTriggerPositionGet(self,
                                             hdwf : c_int,
                                             pcSamplesAfterTrigger : POINTER(c_uint)
                                             ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pcSamplesAfterTrigger) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPositionGet
                          )(hdwf, pcSamplesAfterTrigger)
                return iretVal
            return WpFnGeneric(hdwf, pcSamplesAfterTrigger)

        def WpDwfDigitalInTriggerPrefillSet(self,
                                            hdwf : c_int,
                                            cSamplesBeforeTrigger : c_uint
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint)
            def WpFnGeneric(hdwf, cSamplesBeforeTrigger) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPrefillSet
                          )(hdwf, cSamplesBeforeTrigger)
                return iretVal
            return WpFnGeneric(hdwf, cSamplesBeforeTrigger)

        def WpDwfDigitalInTriggerPrefillGet(self,
                                            hdwf : c_int,
                                            pcSamplesBeforeTrigger : POINTER(c_uint)
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pcSamplesBeforeTrigger) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerPrefillGet
                          )(hdwf, pcSamplesBeforeTrigger)
                return iretVal
            return WpFnGeneric(hdwf, pcSamplesBeforeTrigger)

        def WpDwfDigitalInTriggerAutoTimeoutInfo(self,
                                                 hdwf : c_int,
                                                 psecMin : POINTER(c_double),
                                                 psecMax : POINTER(c_double),
                                                 pnSteps : POINTER(c_double)
                                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double),
                       POINTER(c_double), POINTER(c_double))
            def WpFnGeneric(hdwf, psecMin, psecMax,
                            pnSteps) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerAutoTimeoutInfo
                          )(hdwf, psecMin, psecMax,
                            pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, psecMin, psecMax,
                               pnSteps)

        def WpDwfDigitalInTriggerAutoTimeoutSet(self,
                                                hdwf : c_int,
                                                secTimeout : c_double
                                                ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, secTimeout) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerAutoTimeoutSet
                          )(hdwf, c_double(secTimeout))
                return iretVal
            return WpFnGeneric(hdwf, secTimeout)

        def WpDwfDigitalInTriggerAutoTimeoutGet(self,
                                                hdwf : c_int,
                                                psecTimeout : POINTER(c_double)
                                                ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, psecTimeout) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerAutoTimeoutGet
                          )(hdwf, psecTimeout)
                return iretVal
            return WpFnGeneric(hdwf, psecTimeout)

        def WpDwfDigitalInTriggerInfo(self,
                                      hdwf : c_int,
                                      pfsLevelLow : POINTER(c_uint),
                                      pfsLevelHigh : POINTER(c_uint),
                                      pfsEdgeRise : POINTER(c_uint),
                                      pfsEdgeFall : POINTER(c_uint)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint),
                       POINTER(c_uint), POINTER(c_uint), POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsLevelLow, pfsLevelHigh,
                            pfsEdgeRise, pfsEdgeFall) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerInfo
                          )(hdwf, pfsLevelLow, pfsLevelHigh,
                            pfsEdgeRise, pfsEdgeFall)
                return iretVal
            return WpFnGeneric(hdwf, pfsLevelLow, pfsLevelHigh,
                               pfsEdgeRise, pfsEdgeFall)

        def WpDwfDigitalInTriggerSet(self,
                                     hdwf : c_int,
                                     fsLevelLow : c_uint,
                                     fsLevelHigh : c_uint,
                                     fsEdgeRise : c_uint,
                                     fsEdgeFall : c_uint
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint,
                       c_uint, c_uint, c_uint)
            def WpFnGeneric(hdwf, fsLevelLow, fsLevelHigh,
                            fsEdgeRise, fsEdgeFall) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSet
                          )(hdwf, fsLevelLow, fsLevelHigh,
                            fsEdgeRise, fsEdgeFall)
                return iretVal
            return WpFnGeneric(hdwf, fsLevelLow, fsLevelHigh,
                               fsEdgeRise, fsEdgeFall)

        def WpDwfDigitalInTriggerGet(self,
                                     hdwf : c_int,
                                     pfsLevelLow : POINTER(c_uint),
                                     pfsLevelHigh : POINTER(c_uint),
                                     pfsEdgeRise : POINTER(c_uint),
                                     pfsEdgeFall : POINTER(c_uint)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint),
                       POINTER(c_uint), POINTER(c_uint), POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsLevelLow, pfsLevelHigh,
                            pfsEdgeRise, pfsEdgeFall) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerGet
                          )(hdwf, pfsLevelLow, pfsLevelHigh,
                            pfsEdgeRise, pfsEdgeFall)
                return iretVal
            return WpFnGeneric(hdwf, pfsLevelLow, pfsLevelHigh,
                               pfsEdgeRise, pfsEdgeFall)

        def WpDwfDigitalInTriggerInfo64(self,
                                        hdwf : c_int,
                                        pfsLevelLow : POINTER(c_ulonglong),
                                        pfsLevelHigh : POINTER(c_ulonglong),
                                        pfsEdgeRise : POINTER(c_ulonglong),
                                        pfsEdgeFall : POINTER(c_ulonglong)
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ulonglong),
                       POINTER(c_ulonglong), POINTER(c_ulonglong), POINTER(c_ulonglong))
            def WpFnGeneric(hdwf, pfsLevelLow, pfsLevelHigh,
                            pfsEdgeRise, pfsEdgeFall) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerInfo64
                          )(hdwf, pfsLevelLow, pfsLevelHigh,
                            pfsEdgeRise, pfsEdgeFall)
                return iretVal
            return WpFnGeneric(hdwf, pfsLevelLow, pfsLevelHigh,
                               pfsEdgeRise, pfsEdgeFall)

        def WpDwfDigitalInTriggerSet64(self,
                                       hdwf : c_int,
                                       fsLevelLow : c_ulonglong,
                                       fsLevelHigh : c_ulonglong,
                                       fsEdgeRise : c_ulonglong,
                                       fsEdgeFall : c_ulonglong
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ulonglong,
                       c_ulonglong, c_ulonglong, c_ulonglong)
            def WpFnGeneric(hdwf, ) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerSet64
                          )(hdwf, fsLevelLow, fsLevelHigh,
                            fsEdgeRise, fsEdgeFall)
                return iretVal
            return WpFnGeneric(hdwf, fsLevelLow, fsLevelHigh,
                               fsEdgeRise, fsEdgeFall)

        def WpDwfDigitalInTriggerGet64(self,
                                       hdwf : c_int,
                                       pfsLevelLow : POINTER(c_ulonglong),
                                       pfsLevelHigh : POINTER(c_ulonglong),
                                       pfsEdgeRise : POINTER(c_ulonglong),
                                       pfsEdgeFall : POINTER(c_ulonglong)
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ulonglong),
                       POINTER(c_ulonglong), POINTER(c_ulonglong), POINTER(c_ulonglong))
            def WpFnGeneric(hdwf, pfsLevelLow, pfsLevelHigh,
                            pfsEdgeRise, pfsEdgeFall) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerGet64
                          )(hdwf, pfsLevelLow, pfsLevelHigh,
                            pfsEdgeRise, pfsEdgeFall)
                return iretVal
            return WpFnGeneric(hdwf, pfsLevelLow, pfsLevelHigh,
                               pfsEdgeRise, pfsEdgeFall)

        def WpDwfDigitalInTriggerResetSet(self,
                                          hdwf : c_int,
                                          fsLevelLow : c_uint,
                                          fsLevelHigh : c_uint,
                                          fsEdgeRise : c_uint,
                                          fsEdgeFall : c_uint
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint,
                       c_uint, c_uint, c_uint)
            def WpFnGeneric(hdwf, fsLevelLow, fsLevelHigh,
                            fsEdgeRise, fsEdgeFall) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerResetSet
                          )(hdwf, fsLevelLow, fsLevelHigh,
                            fsEdgeRise, fsEdgeFall)
                return iretVal
            return WpFnGeneric(hdwf, fsLevelLow, fsLevelHigh,
                               fsEdgeRise, fsEdgeFall)

        def WpDwfDigitalInTriggerResetSet64(self,
                                            hdwf : c_int,
                                            fsLevelLow : c_ulonglong,
                                            fsLevelHigh : c_ulonglong,
                                            fsEdgeRise : c_ulonglong,
                                            fsEdgeFall : c_ulonglong
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ulonglong,
                       c_ulonglong, c_ulonglong)
            def WpFnGeneric(hdwf, fsLevelLow, fsLevelHigh,
                            fsEdgeRise, fsEdgeFall) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerResetSet64
                          )(hdwf, fsLevelLow, fsLevelHigh,
                            fsEdgeRise, fsEdgeFall)
                return iretVal
            return WpFnGeneric(hdwf, fsLevelLow, fsLevelHigh,
                               fsEdgeRise, fsEdgeFall)

        def WpDwfDigitalInTriggerCountSet(self,
                                          hdwf : c_int,
                                          cCount : c_int,
                                          fRestart : c_int
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int, c_int)
            def WpFnGeneric(hdwf, cCount, fRestart) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerCountSet
                          )(hdwf, cCount, fRestart)
                return iretVal
            return WpFnGeneric(hdwf, cCount, fRestart)

        def WpDwfDigitalInTriggerLengthSet(self,
                                           hdwf : c_int,
                                           secMin : c_double,
                                           secMax : c_double,
                                           idxSync : c_int
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double,
                       c_double, c_int)
            def WpFnGeneric(hdwf, secMin, secMax,
                            idxSync) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerLengthSet
                          )(hdwf, c_double(secMin), c_double(secMax),
                            idxSync)
                return iretVal
            return WpFnGeneric(hdwf, secMin, secMax,
                               idxSync)

        def WpDwfDigitalInTriggerMatchSet(self,
                                          hdwf : c_int,
                                          iPin : c_int,
                                          fsMask : c_uint,
                                          fsValue : c_uint,
                                          cBitStuffing : c_int
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_uint, c_int)
            def WpFnGeneric(hdwf, iPin, fsMask,
                            fsValue, cBitStuffing) -> int:
                iretVal = self.dtFuncLA.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalInTriggerMatchSet
                          )(hdwf, iPin, fsMask,
                            fsValue, cBitStuffing)
                return iretVal
            return WpFnGeneric(hdwf, iPin, fsMask,
                               fsValue, cBitStuffing)

        def cntrlDigitalInStatus(self,
                                 dStatus : dict
                                 ) -> int:
            """
            @Description
            Status options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions that will be used from settingsinstruments.py.
            @Parameters
            dBuffer : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Status control.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dStatus.keys())
            if not ("Status" in lsKeys or
                    "SamplesLeft" in lsKeys or
                    "SamplesValid" in lsKeys or
                    "IndexWrite" in lsKeys or
                    "AutoTriggered" in lsKeys or
                    "Data" in lsKeys or
                    "Data2" in lsKeys or
                    "Data3" in lsKeys or
                    "Noise2" in lsKeys or
                    "Noise3" in lsKeys or
                    "Record" in lsKeys or
                    "Compress" in lsKeys or
                    "Compressed" in lsKeys or
                    "Compressed2" in lsKeys or
                    "Time" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dStatus["Status"]:
                iRet = self.WpDwfDigitalInStatus(
                            self.iHnd,
                            self.fReadData,
                            self.retSts
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["SamplesLeft"]:
                iRet = self.WpDwfDigitalInStatusSamplesLeft(
                            self.iHnd,
                            self.retSamplesLeft
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["SamplesValid"]:
                iRet = self.WpDwfDigitalInStatusSamplesValid(
                            self.iHnd,
                            self.retSamplesValid
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["IndexWrite"]:
                iRet = self.WpDwfDigitalInStatusIndexWrite(
                            self.iHnd,
                            self.retIdxWrite
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["AutoTriggered"]:
                iRet = self.WpDwfDigitalInStatusAutoTriggered(
                            self.iHnd,
                            self.retAuto
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Data"]:
                iRet = self.WpDwfDigitalInStatusData(
                            self.iHnd,
                            self.rgData,
                            self.iCountOfBytes
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Data2"]:
                iRet = self.WpDwfDigitalInStatusData2(
                            self.iHnd,
                            self.rgData,
                            self.idxSample,
                            self.iCountOfBytes
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Data3"]:
                iRet = self.WpDwfDigitalInStatusData3(
                            self.iHnd,
                            self.rgData,
                            self.idxChannel,
                            self.iCountOfBytes,
                            self.bitShift
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Noise2"]:
                iRet = self.WpDwfDigitalInStatusNoise2(
                            self.iHnd,
                            self.rgData,
                            self.idxSample,
                            self.iCountOfBytes
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Noise3"]:
                iRet = self.WpDwfDigitalInStatusNoise3(
                            self.iHnd,
                            self.rgData,
                            self.idxSample,
                            self.iCountOfBytes,
                            self.bitShift
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Record"]:
                iRet = self.WpDwfDigitalInStatusRecord(
                            self.iHnd,
                            self.cdDataAvailable,
                            self.cdDataLost,
                            self.cdDataCorrupt
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Compress"]:
                iRet = self.WpDwfDigitalInStatusCompress(
                            self.iHnd,
                            self.cdDataAvailable,
                            sefl.cdDataLost,
                            self.cdDataCorrupt,
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Compressed"]:
                iRet = self.WpDwfDigitalInStatusCompressed(
                            self.iHnd,
                            self.rgData,
                            self.iCountOfBytes
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Compressed2"]:
                iRet = self.WpDwfDigitalInStatusCompressed2(
                            self.iHnd,
                            self.rgData,
                            self.idxSample,
                            self.iCountOfBytes
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Time"]:
                iRet = self.WpDwfDigitalInStatusTime(
                            self.iHnd,
                            self.retUiSecUtc,
                            self.retUiTick,
                            self.retUiTicksPerSecond
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalInCounter(self,
                                  dCounter : dict,
                                  bSet : bool,
                                  bGet : bool
                                  ) -> int:
            """
            @Description
            Counter options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions that will be used from settingsinstruments.py.
            @Parameters
            dBuffer : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Counter control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dCounter.keys())
            if not ("Info" in lsKeys or
                    "Status" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dCounter["Info"]:
                iRet = self.WpDwfDigitalInCounterInfo(
                            self.iHnd,
                            self.retCntMax,
                            self.retSecMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalInCounterSet(
                            self.iHnd,
                            self.sec
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalInCounterGet(
                            self.iHnd,
                            self.retSec
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dCounter["Status"]:
                iRet = self.WpDwfDigitalInCounterStatus(
                            self.iHnd,
                            self.retCnt,
                            self.retFreq,
                            self.retTick
                            )
                if iRet & MASK_STATUS == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalInClock(self,
                                dClock : dict,
                                bSet : bool,
                                bGet : bool
                                ) -> int:
            """
            @Description
            Clock options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions that will be used from settingsinstruments.py.
            @Parameters
            dBuffer : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Clock control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dClock.keys())
            if not ("Info" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dClock["Info"]:
                iRet = self.WpDwfDigitalInClockSourceInfo(
                            self.iHnd,
                            self.retFsDwfDigitalInClockSource # use IsBitSet
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalInClockSourceSet(
                            self.iHnd,
                            self.uiClockSource
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalInClockSourceGet(
                            self.iHnd,
                            self.retUiClockSource
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalInDivider(self,
                                  dDivider : dict,
                                  bSet : bool,
                                  bGet : bool
                                  ) -> int:
            """
            @Description
            Divider options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions that will be used from settingsinstruments.py.
            @Parameters
            dBuffer : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Divider control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dDivider.keys())
            if not ("Info" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dDivider["Info"]:
                iRet = self.WpDwfDigitalInDividerInfo(
                            self.iHnd,
                            self.retDivMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalInDividerSet(
                            self.iHnd,
                            self.div
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalInDividerGet(
                            self.iHnd,
                            self.retDiv
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalInSample(self,
                                 dSample : dict,
                                 bSet : bool,
                                 bGet : bool
                                 ) -> int:
            """
            @Description
            Sample options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions that will be used from settingsinstruments.py.
            @Parameters
            dSample : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Sample control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dSample.keys())
            if not ("ModeInfo" in lsKeys or
                    "Format" in lsKeys or
                    "Mode" in lsKeys or
                    "Sensible" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dSample["ModeInfo"]:
                iRet = self.WpDwfDigitalInSampleModeInfo(
                            self.iHnd,
                            self.retFsDwfDigitalInSampleMode
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dSample["Format"]:
                if bSet:
                    iRet = self.WpDwfDigitalInSampleFormatSet(
                                self.iHnd,
                                self.nBits
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInSampleFormatGet(
                                self.iHnd,
                                self.retNBits
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dSample["Mode"]:
                if bSet:
                    iRet = self.WpDwfDigitalInSampleModeSet(
                                self.iHnd,
                                self.inSampleMode
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInSampleModeGet(
                                self.iHnd,
                                self.retInSampleMode
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dSample["Sensible"]:
                if bSet:
                    iRet = self.WpDwfDigitalInSampleSensibleSet(
                                self.iHnd,
                                self.uiFs
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInSampleSensibleGet(
                                self.iHnd,
                                self.retUiFs
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalInBuffer(self,
                                 dBuffer : dict,
                                 bSet : bool,
                                 bGet : bool
                                 ) -> int:
            """
            @Description
            Buffer options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions that will be used from settingsinstruments.py.
            @Parameters
            dBuffer : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Buffer control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dBuffer.keys())
            if not ("SizeInfo" in lsKeys or
                    "Info" in lsKeys or
                    "Status" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dBuffer["SizeInfo"]:
                iRet = self.WpDwfDigitalInBufferSizeInfo(
                            self.iHnd,
                            self.retNSizeMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                
                if bSet:
                    iRet = self.WpDwfDigitalInBufferSizeSet(
                                self.iHnd,
                                self.nSize
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInBufferSizeGet(
                                self.iHnd,
                                self.retNSize
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dBuffer["Info"]:
                iRet = self.WpDwfDigitalInBuffersInfo(
                            self.iHnd,
                            self.retMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                
                if bSet:
                    iRet = self.WpDwfDigitalInBuffersSet(
                                self.iHnd,
                                self.iN
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInBuffersGet(
                                self.iHnd,
                                self.retIN
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dBuffer["Status"]:
                iRet = self.WpDwfDigitalInBuffersStatus(
                            sef.iHnd,
                            self.retIN
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalInAcquisition(self,
                                      dAcquisition : dict,
                                      bSet : bool,
                                      bGet : bool
                                      ) -> int:
            """
            @Description
            Acquisition options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions that will be used from settingsinstruments.py.
            @Parameters
            dAcquisition : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Acquisition control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dAcquisition.keys())
            if not ("ModeInfo" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dAcquisition["ModeInfo"]:
                iRet = self.WpDwfDigitalInAcquisitionModeInfo(
                            self.iHnd,
                            self.retiFsacqmode
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalInAcquisitionModeSet(
                            self.iHnd,
                            self.acqmode
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalInAcquisitionModeGet(
                            self.iHnd,
                            self.retAcqmode
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalInTrigger(self,
                                  dTrigger : dict,
                                  bSet : bool,
                                  bGet : bool
                                  ) -> int:
            """
            @Description
            Trigger options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions that will be used from settingsinstruments.py.
            @Parameters
            dTrigger : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Trigger control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dTrigger.keys())
            if not ("Source" in lsKeys or
                    "Slope" in lsKeys or
                    "PositionInfo" in lsKeys or
                    "Prefill" in lsKeys or
                    "TimeoutInfo" in lsKeys or
                    "Info" in lsKeys or
                    "Info64" in lsKeys or
                    "Reset" in lsKeys or
                    "Reset64" in lsKeys or
                    "Count" in lsKeys or
                    "Length" in lsKeys or
                    "Match" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dTrigger["Source"]:
                if bSet:
                    iRet = self.WpDwfDigitalInTriggerSourceSet(
                                self.iHnd,
                                self.trigsrc
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInTriggerSourceGet(
                                self.iHnd,
                                self.retTrigsrc
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dTrigger["Slope"]:
                if bSet:
                    iRet = self.WpDwfDigitalInTriggerSlopeSet(
                                self.iHnd,
                                self.slope
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInTriggerSlopeGet(
                                self.iHnd,
                                self.retSlope
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dTrigger["PositionInfo"]:
                iRet = self.WpDwfDigitalInTriggerPositionInfo(
                            self.iHnd,
                            self.retNSamplesAfterTriggerMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                
                if bSet:
                    iRet = self.WpDwfDigitalInTriggerPositionSet(
                                self.iHnd,
                                self.cSamplesAfterTrigger
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInTriggerPositionGet(
                                self.iHnd,
                                self.retCSamplesAfterTrigger
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dTrigger["Prefill"]:
                if bSet:
                    iRet = self.WpDwfDigitalInTriggerPrefillSet(
                                self.iHnd,
                                self.cSamplesBeforeTrigger
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInTriggerPrefillGet(
                                self.iHnd,
                                self.retCSamplesBeforeTrigger
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dTrigger["TimeoutInfo"]:
                iRet = self.WpDwfDigitalInTriggerAutoTimeoutInfo(
                            self.iHnd,
                            self.retSecMin,
                            self.retSecMax,
                            self.retNSteps
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                
                if bSet:
                    iRet = self.WpDwfDigitalInTriggerAutoTimeoutSet(
                                self.iHnd,
                                self.secTimeout
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInTriggerAutoTimeoutGet(
                                self.iHnd,
                                self.retSecTimeout
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dTrigger["Info"]:
                iRet = self.WpDwfDigitalInTriggerInfo(
                            self.iHnd,
                            self.retFsLevelLow,
                            self.retFsLevelHigh,
                            self.retFsEdgeRise,
                            self.retFsEdgeFall
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                
                if bSet:
                    iRet = self.WpDwfDigitalInTriggerSet(
                                self.iHnd,
                                self.fsLevelLow,
                                self.fsLevelHigh,
                                self.fsEdgeRise,
                                self.fsEdgeFall
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInTriggerGet(
                                self.iHnd,
                                self.retFsLevelLow,
                                self.retFsLevelHigh,
                                self.retFsEdgeRise,
                                self.retFsEdgeFall
                                )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dTrigger["Info64"]:
                iRet = self.WpDwfDigitalInTriggerInfo64(
                            self.iHnd,
                            self.retllFsLevelLow,
                            self.retllFsLevelHigh,
                            self.retllFsEdgeRise,
                            self.retllFsEdgeFall
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                
                if bSet:
                    iRet = self.WpDwfDigitalInTriggerSet64(
                                self.iHnd,
                                self.llFsLevelLow,
                                self.llFsLevelHigh,
                                self.llFsEdgeRise,
                                self.llFsEdgeFall
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalInTriggerGet64(
                                self.iHnd,
                                self.retllFsLevelLow,
                                self.retllFsLevelHigh,
                                self.retllFsEdgeRise,
                                self.retllFsEdgeFall
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dTrigger["Reset"] and bSet:
                iRet = self.WpDwfDigitalInTriggerResetSet(
                            self.iHnd,
                            self.fsLevelLow,
                            self.fsLevelHigh,
                            self.fsEdgeRise,
                            self.fsEdgeFall
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif dTrigger["Reset64"] and bSet:
                iRet = self.WpDwfDigitalInTriggerResetSet64(
                            self.iHnd,
                            self.llFsLevelLow,
                            self.llFsLevelHigh,
                            self.llFsEdgeRise,
                            self.llFsEdgeFall
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dTrigger["Count"] and bSet:
                iRet = self.WpDwfDigitalInTriggerCountSet(
                            self.iHnd,
                            self.cCount,
                            self.fRestart
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dTrigger["Length"] and bSet:
                iRet = self.WpDwfDigitalInTriggerLengthSet(
                            self.iHnd,
                            self.secMin,
                            self.secMax,
                            self.idxSync
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dTrigger["Match"] and bSet:
                iRet = self.WpDwfDigitalInTriggerMatchSet(
                            self.iHnd,
                            self.iPin,
                            self.fsMask,
                            self.fsValue,
                            self.cBitStuffing
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def Status(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalInStatus()
            pass

        def Counter(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalInCounter()
            pass

        def Clock(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalInClock()
            pass

        def Divider(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalInDivider()
            pass

        def Sample(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalInSample()
            pass

        def Buffer(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalInBuffer()
            pass

        def Acquisition(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalInAcquisition()
            pass

        def Trigger(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalInTrigger()
            pass

    class PatternGeneratorConfig:
        """
        Pattern resources for a single device are encapsulated
        here which can be used for more than one device. Its handler
        is stored then an IO instance is created, so the functions
        that are intended to be used are cntrlDigitalOut,
        cntrlDigitalOutStatus, cntrlDigitalOutTrigger, cntrlDigitalOutRun,
        cntrlDigitalOutWait, cntrlDigitalOutRepeat, cntrlDigitalOutIdle,
        cntrlDigitalOutCounter, cntrlDigitalOutRepetition, cntrlDigitalOutData,
        these use the wrapper functions that starts with WpDwf... .
        @Notes
        Functions with the prefix WpDwf... can be used, but they
        only encapsulate ctypes library, which is of use for
        waveforms' runtime library, to use python built-in types and
        build setups independently of waveforms application.
        """
        def __init__(self,
                     iHnd : c_int
                     ):
            self.pg = PatternGenerator()
            self.dtFuncPG = self.pg.dtFuncPG
            # Parameters for a device's DigitalOut instrument, these
            # are stored in PatternGeneratorConfig object.
            self.iHnd = iHnd
            self.fStart = c_int(0)
            self.retSts = c_ubyte(0)
            self.retFsValue, self.retFsEnable = c_uint(0), c_uint(0)
            self.retHzFreq = c_double(0.0)
            self.trigsrc = c_ubyte(0)
            self.retTrigsrc = c_ubyte(0)
            self.retSecMin, self.retSecMax = c_double(0.0), c_double(0.0)
            self.secRun = c_double(0.0)
            self.retSecRun = c_double(0.0)
            self.secWait = c_double(0.0)
            self.retSecWait = c_double(0.0)
            self.retNMin, self.retNMax = c_uint(0), c_uint(0)
            self.cRepeat = c_uint(0)
            self.retCRepeat = c_uint(0)
            self.slope = c_int(0)
            self.retSlope = c_int(0)
            self.fRepeatTrigger = c_int(0)
            self.retFRepeatTriggger = c_int(0)
            self.retCChannel = c_int(0)
            self.idxChannel, self.fEnable = c_int(0), c_int(0)
            self.retFsDwfDigitalOutOutput = c_int(0)
            self.vOutput = c_int(0)
            self.retVOutput = c_int(0)
            self.retFsDwfDigitalOutType = c_int(0)
            self.vOutType = c_int(0)
            self.retVOutType = c_int(0)
            self.retFsDwfDigitalOutIdle = c_int(0)
            self.vOutIdle = c_int(0)
            self.retVOutIdle = c_int(0)
            self.retVMin, self.retVMax = c_int(0), c_int(0)
            self.vDividerInit = c_int(0)
            self.retVDividerInit = c_int(0)
            self.vDivider = c_int(0)
            self.retVDivider = c_int(0)
            self.fHigh, self.vCounterInit = c_int(0), c_uint(0)
            self.retFHigh, self.retVCounterInit = c_int(0), c_uint(0)
            self.vLow, self.vHigh = c_uint(0), c_uint(0)
            self.retVLow, self.retVHigh = c_uint(0), c_uint(0)
            self.retNMax = c_uint(0)
            self.cRepeat = c_uint(0)
            self.retCRepeat = c_uint(0)
            self.retCountOfBitsMax = c_uint(0)
            self.vRgBits = (c_ubyte*1)()
            self.countOfBits = c_uint(0)
            self.uRgBits = (c_ubyte*1)()
            self.bitPerSample = c_uint(0)
            self.countOfSamples = c_uint(0)
            self.indexOfSample = c_uint(0)
            self.hzRate = c_double(0.0)

        def WpDwfDigitalOutReset(self,
                                 hdwf : c_int,
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalOutConfigure(self,
                                     hdwf : c_int,
                                     fStart : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fStart) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutConfigure
                          )(hdwf, fStart)
                return iretVal
            return WpFnGeneric(hdwf, fStart)

        def WpDwfDigitalOutStatus(self,
                                  hdwf : c_int,
                                  psts : POINTER(c_ubyte)
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ubyte))
            def WpFnGeneric(hdwf, psts) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutStatus
                          )(hdwf, psts)
                return iretVal
            return WpFnGeneric(hdwf, psts)

        def WpDwfDigitalOutStatusOutput(self,
                                        hdwf : c_int,
                                        pfsValue : POINTER(c_uint),
                                        pfsEnable : POINTER(c_uint)
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint),
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, pfsValue, pfsEnable) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutStatusOutput
                          )(hdwf, pfsValue, pfsEnable)
                return iretVal
            return WpFnGeneric(hdwf, pfsValue, pfsEnable)

        def WpDwfDigitalOutInternalClockInfo(self,
                                             hdwf : c_int,
                                             phzFreq : POINTER(c_double)
                                             ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, phzFreq) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutInternalClockInfo
                          )(hdwf, phzFreq)
                return iretVal
            return WpFnGeneric(hdwf, phzFreq)

        def WpDwfDigitalOutTriggerSourceSet(self,
                                            hdwf : c_int,
                                            trigsrc : c_ubyte
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ubyte)
            def WpFnGeneric(hdwf, trigsrc) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutTriggerSourceSet
                          )(hdwf, trigsrc)
                return iretVal
            return WpFnGeneric(hdwf, trigsrc)

        def WpDwfDigitalOutTriggerSourceGet(self,
                                            hdwf : c_int,
                                            ptrigsrc : POINTER(c_ubyte)
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ubyte))
            def WpFnGeneric(hdwf, ptrigsrc) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutTriggerSourceGet
                          )(hdwf, ptrigsrc)
                return iretVal
            return WpFnGeneric(hdwf, ptrigsrc)

        def WpDwfDigitalOutRunInfo(self,
                                   hdwf : c_int,
                                   psecMin : POINTER(c_double),
                                   psecMax : POINTER(c_double)
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, POINTER(c_double), POINTER(c_double))
            def WpFnGeneric(hdwf, psecMin, psecMax) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRunInfo
                          )(hdwf, psecMin, psecMax)
                return iretVal
            return WpFnGeneric(hdwf, psecMin, psecMax)

        def WpDwfDigitalOutRunSet(self,
                                  hdwf : c_int,
                                  secRun : c_double
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, secRun) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRunSet
                          )(hdwf, c_double(secRun))
                return iretVal
            return WpFnGeneric(hdwf, secRun)

        def WpDwfDigitalOutRunGet(self,
                                  hdwf : c_int,
                                  psecRun : POINTER(c_double)
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, psecRun) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRunGet
                          )(hdwf, psecRun)
                return iretVal
            return WpFnGeneric(hdwf, psecRun)

        def WpDwfDigitalOutRunStatus(self,
                                     hdwf : c_int,
                                     psecRun : POINTER(c_double)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, psecRun) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRunStatus
                          )(hdwf, psecRun)
                return iretVal
            return WpFnGeneric(hdwf, psecRun)

        def WpDwfDigitalOutWaitInfo(self,
                                    hdwf : c_int,
                                    psecMin : POINTER(c_double),
                                    psecMax : POINTER(c_double)
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double),
                       POINTER(c_double))
            def WpFnGeneric(hdwf, psecMin, psecMax) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutWaitInfo
                          )(hdwf, psecMin, psecMax)
                return iretVal
            return WpFnGeneric(hdwf, psecMin, psecMax)

        def WpDwfDigitalOutWaitSet(self,
                                   hdwf : c_int,
                                   secWait : c_double
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, secWait) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutWaitSet
                          )(hdwf, c_double(secWait))
                return iretVal
            return WpFnGeneric(hdwf, secWait)

        def WpDwfDigitalOutWaitGet(self,
                                   hdwf : c_int,
                                   psecWait : POINTER(c_double)
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, psecWait) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutWaitGet
                          )(hdwf, psecWait)
                return iretVal
            return WpFnGeneric(hdwf, psecWait)

        def WpDwfDigitalOutRepeatInfo(self,
                                      hdwf : c_int,
                                      pnMin : POINTER(c_uint),
                                      pnMax : POINTER(c_uint)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint),
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, pnMin, pnMax) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatInfo
                          )(hdwf, pnMin, pnMax)
                return iretVal
            return WpFnGeneric(hdwf, pnMin, pnMax)

        def WpDwfDigitalOutRepeatSet(self,
                                     hdwf : c_int,
                                     cRepeat : c_uint
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint)
            def WpFnGeneric(hdwf, cRepeat) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatSet
                          )(hdwf, cRepeat)
                return iretVal
            return WpFnGeneric(hdwf, cRepeat)

        def WpDwfDigitalOutRepeatGet(self,
                                     hdwf : c_int,
                                     pcRepeat : POINTER(c_uint)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pcRepeat) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatGet
                          )(hdwf, pcRepeat)
                return iretVal
            return WpFnGeneric(hdwf, pcRepeat)

        def WpDwfDigitalOutRepeatStatus(self,
                                        hdwf : c_int,
                                        pcRepeat : POINTER(c_uint)
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, pcRepeat) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatStatus
                          )(hdwf, pcRepeat)
                return iretVal
            return WpFnGeneric(hdwf, pcRepeat)

        def WpDwfDigitalOutTriggerSlopeSet(self,
                                           hdwf : c_int,
                                           slope : c_int
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, slope) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutTriggerSlopeSet
                          )(hdwf, slope)
                return iretVal
            return WpFnGeneric(hdwf, slope)

        def WpDwfDigitalOutTriggerSlopeGet(self,
                                            hdwf : c_int,
                                            pslope : POINTER(c_int)
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pslope) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutTriggerSlopeGet
                          )(hdwf, pslope)
                return iretVal
            return WpFnGeneric(hdwf, pslope)

        def WpDwfDigitalOutRepeatTriggerSet(self,
                                            hdwf : c_int,
                                            fRepeatTrigger : c_int
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fRepeatTrigger) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatTriggerSet
                          )(hdwf, fRepeatTrigger)
                return iretVal
            return WpFnGeneric(hdwf, fRepeatTrigger)

        def WpDwfDigitalOutRepeatTriggerGet(self,
                                            hdwf : c_int,
                                            pfRepeatTrigger : POINTER(c_int)
                                            ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfRepeatTrigger) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepeatTriggerGet
                          )(hdwf, pfRepeatTrigger)
                return iretVal
            return WpFnGeneric(hdwf, pfRepeatTrigger)

        def WpDwfDigitalOutCount(self,
                                 hdwf : c_int,
                                 pcChannel : POINTER(c_int)
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pcChannel) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutCount
                          )(hdwf, pcChannel)
                return iretVal
            return WpFnGeneric(hdwf, pcChannel)

        def WpDwfDigitalOutEnableSet(self,
                                     hdwf : c_int,
                                     idxChannel : c_int,
                                     fEnable : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int)
            def WpFnGeneric(hdwf, idxChannel, fEnable) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutEnableSet
                          )(hdwf, idxChannel, fEnable)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, fEnable)

        def WpDwfDigitalOutEnableGet(self,
                                     hdwf : c_int,
                                     idxChannel : c_int,
                                     pfEnable : POINTER(c_int)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, pfEnable) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutEnableGet
                          )(hdwf, idxChannel, pfEnable)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pfEnable)

        def WpDwfDigitalOutOutputInfo(self,
                                      hdwf : c_int,
                                      idxChannel : c_int,
                                      pfsDwfDigitalOutOutput : POINTER(c_int)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, pfsDwfDigitalOutOutput) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutOutputInfo
                          )(hdwf, idxChannel, pfsDwfDigitalOutOutput)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pfsDwfDigitalOutOutput)

        def WpDwfDigitalOutOutputSet(self,
                                     hdwf : c_int,
                                     idxChannel : c_int,
                                     v : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int)
            def WpFnGeneric(hdwf, idxChannel, v) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutOutputSet
                          )(hdwf, idxChannel, v)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, v)

        def WpDwfDigitalOutOutputGet(self,
                                     hdwf : c_int,
                                     idxChannel : c_int,
                                     pv : POINTER(c_int)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, pv) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutOutputGet
                          )(hdwf, idxChannel, pv)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pv)

        def WpDwfDigitalOutTypeInfo(self,
                                    hdwf : c_int,
                                    idxChannel : c_int,
                                    pfsDwfDigitalOutType : POINTER(c_int)
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, pfsDwfDigitalOutType) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutTypeInfo
                          )(hdwf, idxChannel, pfsDwfDigitalOutType)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pfsDwfDigitalOutType)

        def WpDwfDigitalOutTypeSet(self,
                                   hdwf : c_int,
                                   idxChannel : c_int,
                                   v : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel, v) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutTypeSet
                          )(hdwf, idxChannel, v)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, v)

        def WpDwfDigitalOutTypeGet(self,
                                   hdwf : c_int,
                                   idxChannel : c_int,
                                   pv : POINTER(c_int)
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, pv) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutTypeGet
                          )(hdwf, idxChannel, pv)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pv)

        def WpDwfDigitalOutIdleInfo(self,
                                    hdwf : c_int,
                                    idxChannel : c_int,
                                    pfsDwfDigitalOutIdle : POINTER(c_int)
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, pfsDwfDigitalOutIdle) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutIdleInfo
                          )(hdwf, idxChannel, pfsDwfDigitalOutIdle)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pfsDwfDigitalOutIdle)

        def WpDwfDigitalOutIdleSet(self,
                                   hdwf : c_int,
                                   idxChannel : c_int,
                                   v : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel, v) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutIdleSet
                          )(hdwf, idxChannel, v)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, v)

        def WpDwfDigitalOutIdleGet(self,
                                   hdwf : c_int,
                                   idxChannel : c_int,
                                   pv : POINTER(c_int)
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, pv) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutIdleGet
                          )(hdwf, idxChannel, pv)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pv)

        def WpDwfDigitalOutDividerInfo(self,
                                       hdwf : c_int,
                                       idxChannel : c_int,
                                       vMin : POINTER(c_uint),
                                       vMax : POINTER(c_uint)
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_uint), POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, vMin,
                            vMax) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerInfo
                          )(hdwf, idxChannel, vMin,
                            vMax)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, vMin,
                               vMax)

        def WpDwfDigitalOutDividerInitSet(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          v : c_uint
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint)
            def WpFnGeneric(hdwf, idxChannel, v) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerInitSet
                          )(hdwf, idxChannel, v)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, v)

        def WpDwfDigitalOutDividerInitGet(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          pv : POINTER(c_uint)
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, pv) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerInitGet
                          )(hdwf, idxChannel, pv)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pv)

        def WpDwfDigitalOutDividerSet(self,
                                      hdwf : c_int,
                                      idxChannel : c_int,
                                      v : c_uint
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint)
            def WpFnGeneric(hdwf, idxChannel, v) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerSet
                          )(hdwf, idxChannel, v)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, v)

        def WpDwfDigitalOutDividerGet(self,
                                      hdwf : c_int,
                                      idxChannel : c_int,
                                      pv : POINTER(c_uint)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, pv) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutDividerGet
                          )(hdwf, idxChannel, pv)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pv)

        def WpDwfDigitalOutCounterInfo(self,
                                       hdwf : c_int,
                                       idxChannel : c_int,
                                       vMin : POINTER(c_uint),
                                       vMax : POINTER(c_uint)
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_uint),
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, vMin,
                            vMax) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterInfo
                          )(hdwf, idxChannel, vMin,
                            vMax)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, vMin,
                               vMax)

        def WpDwfDigitalOutCounterInitSet(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          fHigh : c_int,
                                          v : c_uint
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint)
            def WpFnGeneric(hdwf, idxChannel, fHigh,
                            v) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterInitSet
                          )(hdwf, idxChannel, fHigh,
                            v)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, fHigh,
                               v)

        def WpDwfDigitalOutCounterInitGet(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          pfHigh : POINTER(c_int),
                                          pv : POINTER(c_uint)
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int),
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, pfHigh,
                            pv) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterInitGet
                          )(hdwf, idxChannel, pfHigh,
                            pv)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pfHigh,
                               pv)

        def WpDwfDigitalOutCounterSet(self,
                                      hdwf : c_int,
                                      idxChannel : c_int,
                                      vLow : c_uint,
                                      vHigh : c_uint
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_uint)
            def WpFnGeneric(hdwf, idxChannel, vLow,
                            vHigh) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterSet
                          )(hdwf, idxChannel, vLow,
                            vHigh)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, vLow,
                               vHigh)

        def WpDwfDigitalOutCounterGet(self,
                                      hdwf : c_int,
                                      idxChannel : c_int,
                                      pvLow : POINTER(c_uint),
                                      pvHigh : POINTER(c_uint)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_uint), POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, pvLow,
                            pvHigh) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutCounterGet
                          )(hdwf, idxChannel, pvLow,
                            pvHigh)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pvLow,
                               pvHigh)

        def WpDwfDigitalOutRepetitionInfo(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          pnMax : POINTER(c_uint)
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, pnMax) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepetitionInfo
                          )(hdwf, idxChannel, pnMax)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pnMax)

        def WpDwfDigitalOutRepetitionSet(self,
                                         hdwf : c_int,
                                         idxChannel : c_int,
                                         cRepeat : c_uint
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint)
            def WpFnGeneric(hdwf, idxChannel, cRepeat) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepetitionSet
                          )(hdwf, idxChannel, cRepeat)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, cRepeat)

        def WpDwfDigitalOutRepetitionGet(self,
                                         hdwf : c_int,
                                         idxChannel : c_int,
                                         pcRepeat : POINTER(c_uint)
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, pcRepeat) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutRepetitionGet
                          )(hdwf, idxChannel, pcRepeat)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pcRepeat)

        def WpDwfDigitalOutDataInfo(self,
                                    hdwf : c_int,
                                    idxChannel : c_int,
                                    pcountOfBitsMax : POINTER(c_uint)
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_uint))
            def WpFnGeneric(hdwf, idxChannel, pcountOfBitsMax) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutDataInfo
                          )(hdwf, idxChannel, pcountOfBitsMax)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pcountOfBitsMax)

        def WpDwfDigitalOutDataSet(self,
                                   hdwf : c_int,
                                   idxChannel : c_int,
                                   rgBits : POINTER(c_void_p),
                                   countOfBits : c_uint
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_void_p), c_uint)
            def WpFnGeneric(hdwf, idxChannel, rgBits,
                            countOfBits) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutDataSet
                          )(hdwf, idxChannel, rgBits,
                            countOfBits)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, rgBits,
                               countOfBits)

        def WpDwfDigitalOutPlayDataSet(self,
                                       hdwf : c_int,
                                       rgBits : POINTER(c_ubyte),
                                       bitPerSample : c_uint,
                                       countOfSamples : c_uint
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ubyte),
                       c_uint, c_uint)
            def WpFnGeneric(hdwf, rgBits, bitPerSample,
                            countOfSamples) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutPlayDataSet
                          )(hdwf, rgBits, bitPerSample,
                            countOfSamples)
                return iretVal
            return WpFnGeneric(hdwf, rgBits, bitPerSample,
                               countOfSamples)

        def WpDwfDigitalOutPlayUpdateSet(self,
                                         hdwf : c_int,
                                         rgBits : POINTER(c_ubyte),
                                         indexOfSample : c_uint,
                                         countOfSamples : c_uint
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ubyte),
                       c_uint, c_uint)
            def WpFnGeneric(hdwf, rgBits, indexOfSample,
                            countOfSamples) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutPlayUpdateSet
                          )(hdwf, rgBits, indexOfSample,
                            countOfSamples)
                return iretVal
            return WpFnGeneric(hdwf, rgBits, indexOfSample,
                               countOfSamples)

        def WpDwfDigitalOutPlayRateSet(self,
                                       hdwf : c_int,
                                       hzRate : c_double
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, hzRate) -> int:
                iretVal = self.dtFuncPG.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalOutPlayRateSet
                          )(hdwf, c_double(hzRate))
                return iretVal
            return WpFnGeneric(hdwf, hzRate)

        def cntrlDigitalOut(self,
                            dDO : dict
                            ) -> int:
            """
            @Description
            DigitalOut options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dDO : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain DigitalOut control.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dDO.keys())
            if not ("Reset" in lsKeys or
                    "Configure" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dDO["Reset"]:
                iRet = self.WpDwfDigitalOutReset(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dDO["Configure"]:
                iRet = self.WpDwfDigitalOutConfigure(
                            self.iHnd,
                            self.fStart
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutStatus(self,
                                  dStatus : dict
                                  ) -> int:
            """
            @Description
            Status options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dDO : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Status control.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dStatus.keys())
            if not ("Status" in lsKeys or
                    "Output" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dStatus["Status"]:
                iRet = self.WpDwfDigitalOutStatus(
                            self.iHnd,
                            self.retSts
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dStatus["Output"]:
                iRet = self.WpDwfDigitalOutStatusOutput(
                            self.iHnd,
                            self.retFsValue,
                            self.retFsEnable
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutTrigger(self,
                                   dTrigger : dict,
                                   bSet : bool,
                                   bGet : bool
                                   ) -> int:
            """
            @Description
            Trigger options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dTrigger : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Trigger control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dTrigger.keys())
            if not ("Source" in lsKeys or
                    "Slope" in lsKeys or
                    "Repeat" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dTrigger["Source"]:
                if bSet:
                    iRet = self.WpDwfDigitalOutTriggerSourceSet(
                                self.iHnd,
                                self.trigsrc
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalOutTriggerSourceGet(
                                self.iHnd,
                                self.retTrigsrc
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dTrigger["Slope"]:
                if bSet:
                    iRet = self.WpDwfDigitalOutTriggerSlopeSet(
                                self.iHnd,
                                self.slope
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalOutTriggerSlopeGet(
                                self.iHnd,
                                self.retSlope
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if dTrigger["Repeat"]:
                if bSet:
                    iRet = self.WpDwfDigitalOutRepeatTriggerSet(
                                self.iHnd,
                                self.fRepeatTrigger
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalOutRepeatTriggerGet(
                                self.iHnd,
                                self.retFRepeatTriggger
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutRun(self,
                               dRun : dict,
                               bSet : bool,
                               bGet : bool
                               ) -> int:
            """
            @Description
            Run options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dRun : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Run control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dRun.keys())
            if not ("Info" in lsKeys or
                    "Status" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dRun["Info"]:
                iRet = self.WpDwfDigitalOutRunInfo(
                            self.iHnd,
                            self.retSecMin,
                            self.retSecMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dRun["Status"]:
                iRet = self.WpDwfDigitalOutRunStatus(
                            self.iHnd,
                            self.retSecRun
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalOutRunSet(
                            self.iHnd,
                            self.secRun
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalOutRunGet(
                            self.iHnd,
                            self.retSecRun
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutWait(self,
                                dWait : dict,
                                bSet : bool,
                                bGet : bool
                                ) -> int:
            """
            @Description
            Wait options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dWait : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Wait control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dWait.keys())
            if not ("Info" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dWait["Info"]:
                iRet = self.WpDwfDigitalOutWaitInfo(
                            self.iHnd,
                            self.retSecMin,
                            self.retSecMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalOutWaitSet(
                            self.iHnd,
                            self.secWait
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalOutWaitGet(
                            self.iHnd,
                            self.retSecWait
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutRepeat(self,
                                  dRepeat : dict,
                                  bSet : bool,
                                  bGet : bool
                                  ) -> int:
            """
            @Description
            Repeat options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dRepeat : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Repeat control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dRepeat.keys())
            if not ("Info" in lsKeys or
                    "Status" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dRepeat["Info"]:
                iRet = self.WpDwfDigitalOutRepeatInfo(
                            self.iHnd,
                            self.retNMin,
                            self.retNMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dRepeat["Status"]:
                iRet = self.WpDwfDigitalOutRepeatStatus(
                            self.iHnd,
                            self.retCRepeat
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalOutRepeatSet(
                            self.iHnd,
                            self.cRepeat
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalOutRepeatGet(
                            self.iHnd,
                            self.retCRepeat
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutType(self,
                                dType : dict,
                                bSet : bool,
                                bGet : bool
                                ) -> int:
            """
            @Description
            Type options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dType : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Type control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dType.keys())
            if not ("Info" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dType["Info"]:
                iRet = self.WpDwfDigitalOutTypeInfo(
                            self.iHnd,
                            self.idxChannel,
                            self.retFsDwfDigitalOutType # Use IsBitSet
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalOutTypeSet(
                            self.iHnd,
                            self.vOutType
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalOutTypeGet(
                            self.iHnd,
                            self.retVOutType
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutIdle(self,
                                dIdle : dict,
                                bSet : bool,
                                bGet : bool
                                ) -> int:
            """
            @Description
            Idle options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dIdle : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Idle control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dIdle.keys())
            if not ("Info" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dIdle["Info"]:
                iRet = self.WpDwfDigitalOutIdleInfo(
                            self.iHnd,
                            self.retFsDwfDigitalOutIdle
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalOutIdleSet(
                            self.iHnd,
                            self.vOutIdle
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalOutIdleGet(
                            self.iHnd,
                            self.retVOutIdle
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutDivider(self,
                                   dDivider : dict,
                                   bSet : bool,
                                   bGet : bool
                                   ) -> int:
            """
            @Description
            Divider options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dDivider : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Divider control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dDivider.keys())
            if not ("Info" in lsKeys or
                    "Init" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dDivider["Info"]:
                iRet = self.WpDwfDigitalOutDividerInfo(
                            self.iHnd,
                            self.idxChannel,
                            self.retVMin,
                            self.retVMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dDivider["Init"]:
                if bSet:
                    iRet = self.WpDwfDigitalOutDividerInitSet(
                                self.iHnd,
                                self.idxChannel,
                                self.vDividerInit
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalOutDividerInitGet(
                                self.iHnd,
                                self.idxChannel,
                                self.retVDividerInit
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalOutDividerSet(
                            self.iHnd,
                            self.idxChannel,
                            self.vDivider
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalOutDividerGet(
                            self.iHnd,
                            self.idxChannel,
                            self.retVDivider
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutCounter(self,
                                   dCounter : dict,
                                   bSet : bool,
                                   bGet : bool
                                   ) -> int:
            """
            @Description
            Counter options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dCounter : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Counter control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dCounter.keys())
            if not ("Info" in lsKeys or
                    "Init" in lsKeys or
                    "Count" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dCounter["Info"]:
                iRet = self.WpDwfDigitalOutCounterInfo(
                            self.iHnd,
                            self.idxChannel,
                            self.retVMin,
                            self.retVMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dCounter["Init"]:
                if bSet:
                    iRet = self.WpDwfDigitalOutCounterInitSet(
                                self.iHnd,
                                self.idxChannel,
                                self.fHigh,
                                self.vCounterInit
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                elif bGet:
                    iRet = self.WpDwfDigitalOutCounterInitGet(
                                self.iHnd,
                                self.idxChannel,
                                self.retVCounterInit
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalOutCounterSet(
                            self.iHnd,
                            self.idxChannel,
                            self.vLow,
                            self.vHigh
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalOutCounterGet(
                            self.iHnd,
                            self.idxChannel,
                            self.retVLow,
                            self.retVHigh
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dCounter["Count"]:
                iRet = self.WpDwfDigitalOutCount(
                            self.iHnd,
                            self.retCChannel
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutRepetition(self,
                                      dRepetition : dict,
                                      bSet : bool,
                                      bGet : bool
                                      ) -> int:
            """
            @Description
            Repetition options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dRepetition : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Repetition control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dRepetition.keys())
            if not ("Info" in lsKeys):
                return DigitalInstruments.FAILURE
            
            if dRepetition["Info"]:
                iRet = self.WpDwfDigitalOutRepetitionInfo(
                            self.iHnd,
                            self.idxChannel,
                            self.retNMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if bSet:
                iRet = self.WpDwfDigitalOutRepetitionSet(
                            self.iHnd,
                            self.idxChannel,
                            self.cRepeat
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            elif bGet:
                iRet = self.WpDwfDigitalOutRepetitionGet(
                            self.iHnd,
                            self.idxChannel,
                            self.retCRepeat
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalOutData(self,
                                dData : dict,
                                bSet : bool
                                ) -> int:
            """
            @Description
            Data options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dData : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Data control.
            bSet : Flag for setter functions.
            bGet : Flag for getter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dData.keys())
            if not ("Info" in lsKeys or
                    "Data" in lsKeys or
                    "PlayData" in lsKeys or
                    "PlayUpdate" in lsKeys or
                    "PlayRate" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dData["Info"]:
                iRet = self.WpDwfDigitalOutDataInfo(
                            self.iHnd,
                            self.idxChannel,
                            self.retCountOfBitsMax
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dData["Data"] and bSet:
                iRet = self.WpDwfDigitalOutDataSet(
                            self.iHnd,
                            self.idxChannel,
                            self.urgBits,
                            self.countOfBits
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dData["PlayData"] and bSet:
                iRet = self.WpDwfDigitalOutPlayDataSet(
                            self.iHnd,
                            self.urgBits,
                            self.bitPerSample,
                            self.countOfSamples
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dData["PlayUpdate"] and bSet:
                iRet = self.WpDwfDigitalOutPlayUpdateSet(
                            self.iHnd,
                            self.urgBits,
                            self.indexOfSample,
                            self.countOfSamples
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            if dData["PlayRate"] and bSet:
                iRet = self.WpDwfDigitalOutPlayRateSet(
                            self.iHnd,
                            self.hzRate
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
            
            return DigitalInstruments.SUCCESS

        def Out(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOut()
            pass

        def Status(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutStatus()
            pass

        def Trigger(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutTrigger()
            pass

        def Run(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutRun()
            pass

        def Wait(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutWait()
            pass

        def Repeat(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutRepeat()
            pass

        def Type(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutType()
            pass

        def Idle(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutIdle()
            pass

        def Divider(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutDivider()
            pass

        def Counter(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutCounter()
            pass

        def Repetition(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutRepetition()
            pass

        def Data(self):
            """
            @Description
            @Parameters
            @Return
            @Notes
            """
            #self.cntrlDigitalOutData()
            pass

    class DigitalProtocolsConfig:
        """
        Digital Protocols resources for a single device are encapsulated
        here which can be used for more than one device. Its handler
        is stored then an IO instance is created, so the functions
        that are intended to be used are cntrlDigitalUart,
        cntrlDigitalSpi, cntrlDigitalCan, cntrlDigitalSwd,
        these use the wrapper functions that starts with WpDwf... .
        @Notes
        Functions with the prefix WpDwf... can be used, but they
        only encapsulate ctypes library, which is of use for
        waveforms' runtime library, to use python built-in types and
        build setups independently of waveforms application.
        """
        def __init__(self,
                     iHnd : c_int
                     ):
            self.dp = DigitalProtocols()
            self.dtFuncDP = self.dp.dtFuncDP
            # Parameters for a device's Protocols instrument, these
            # are stored in DigitalProtocolsConfig object.
            self.iHnd = iHnd
            self.hz = c_double(0.0)
            self.cBits = c_int(0)
            self.parity = c_int(0)
            self.polarity = c_int(0)
            self.cBit = c_double(0.0)
            self.idxChannel = c_int(0)
            self.szTx, self.cTx, self.cRx = (c_char*1)(), c_int(0), c_int(0)
            self.retCRx, self.retParity = (c_char*1)(), c_int(0)
            self.hz = c_double(0.0)
            self.idxDQ = c_int(0)
            self.idle = c_int(0)
            self.iMode = c_int(0)
            self.fMSBFirst = c_int(0)
            self.cStart, self.cCmd = c_int(0), c_int(0)
            self.cWord, self.cStop = c_int(0), c_int(0)
            self.idxSelect, self.fIdle = c_int(0), c_int(0)
            self.level = c_int(0)
            self.cDQ, self.cBitPerWord = c_int(0), c_int(0)
            self.ucRgTX, self.ucRgRX = (c_ubyte*1)(), (c_ubyte*1)()
            self.usRgTX, self.usRgRX = (c_ushort*1)(), (c_ushort*1)()
            self.uiRgTX, self.uiRgRX = (c_uint*1)(), (c_uint*1)()
            self.uipRX = (c_uint*1)()
            self.vTX = c_uint(0)
            self.cBitCmd, self.cmd, self.cDummy = c_int(0), c_uint(0), c_int(0)
            self.retFFree = c_int(0)
            self.fEnable = c_int(0)
            self.hz = c_double(0.0)
            self.fNakLastReadByte = c_int(0)
            self.sec = c_double(0.0)
            self.adr8bits, self.ucRgbTx = c_ubyte(0), (c_ubyte*1)()
            self.ucRgbRx, self.retNak = (c_ubyte*1)(), c_int(0)
            self.bTx = c_ubyte(0)
            self.retFStart, self.retFStop, self.ucRgData = c_int(0), c_int(0), (c_ubyte*1)()
            self.icData, self.retINak = c_int(0), c_int(0)
            self.fHigh = c_int(0)
            self.vID, self.fExtended = c_int(0), c_int(0)
            self.fRemote, self.cDLC = c_int(0), c_int(0)
            self.retVID, self.retFExtended, self.retFRemote = c_int(0), c_int(0), c_int(0)
            self.refCDLC, self.VStatus = c_int(0), c_int(0)
            self.cTurn = c_int(0)
            self.cTrail = c_int(0)
            self.fDrive = c_int(0)
            self.fContinue = c_int(0)
            self.cReset = c_int(0)
            self.APnDP, self.A32, self.retAck = c_int(0), c_int(0), c_int(0)
            self.Write = c_uint(0)
            self.retRead, self.retCrc = c_uint(0), c_int(0)
            # Dicts to be used in Uart(), Spi(), I2c(), Can() and Swd()
            # member functions.
            self.auxUart = { "Reset" : False, "Rate" : False,
                             "Bits" : False, "Parity" : False,
                             "Polarity" : False, "Stop" : False,
                             "Tx" : False, "Rx" : False
                             }
            self.auxSpi = { "Reset" : False, "Frequency" : False,
                            "Clock" : False, "Data" : False,
                            "Idle" : False, "Mode" : False,
                            "Order" : False, "Delay" : False,
                            "Select" : False, "Write" : False,
                            "Read" : False, "Write" : False,
                            "WriteRead" : False, "WriteRead16" : False,
                            "WriteRead32" : False, "ReadOne" : False,
                            "Read16" : False, "Read32" : False,
                            "WriteOne" : False, "CmdWriteRead" : False,
                            "CmdWrite16" : False, "CmdWrite32" : False,
                            "CmdRead" : False, "CmdReadOne" : False,
                            "CmdRead16" : False, "CmdRead32" : False
                            }
            self.auxI2c = { "Reset" : False, "Clear" : False,
                            "Stretch" : False, "Rate" : False,
                            "Scl" : False, "Sda" : False,
                            "Timeout" : False, "WriteRead" : False,
                            "Read" : False, "Write" : False,
                            "WriteOne" : False, "SpyStart" : False,
                            "SpyStatus" : False
                            }
            self.auxCan = { "Reset" : False, "Rate" : False,
                            "Polarity" : False, "Tx" : False,
                            "Rx" : False
                            }
            self.auxSwd = { "Reset" : False, "Rate" : False,
                            "Ck" : False, "Io" : False,
                            "Trun" : False, "Trail" : False,
                            "Park" : False, "Nak" : False,
                            "IoIdle" : False, "Clear" : False,
                            "Write" : False, "Read" : False
                            }

        def WpDwfDigitalUartReset(self,
                                  hdwf : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalUartRateSet(self,
                                    hdwf : c_int,
                                    hz : c_double
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, hz) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartRateSet
                          )(hdwf, c_double(hz))
                return iretVal
            return WpFnGeneric(hdwf, hz)

        def WpDwfDigitalUartBitsSet(self,
                                    hdwf : c_int,
                                    cBits : c_int
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, cBits) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartBitsSet
                          )(hdwf, cBits)
                return iretVal
            return WpFnGeneric(hdwf, cBits)

        def WpDwfDigitalUartParitySet(self,
                                      hdwf : c_int,
                                      parity : c_int
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, parity) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartParitySet
                          )(hdwf, parity)
                return iretVal
            return WpFnGeneric(hdwf, parity)

        def WpDwfDigitalUartPolaritySet(self,
                                        hdwf : c_int,
                                        polarity : c_int
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, polarity) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartPolaritySet
                          )(hdwf, polarity)
                return iretVal
            return WpFnGeneric(hdwf, polarity)

        def WpDwfDigitalUartStopSet(self,
                                    hdwf : c_int,
                                    cBit : c_double
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, cBit) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartStopSet
                          )(hdwf, c_double(cBit))
                return iretVal
            return WpFnGeneric(hdwf, cBit)

        def WpDwfDigitalUartTxSet(self,
                                  hdwf : c_int,
                                  idxChannel : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartTxSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalUartRxSet(self,
                                  hdwf : c_int,
                                  idxChannel : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartRxSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalUartTx(self,
                               hdwf : c_int,
                               szTx : POINTER(c_char),
                               cTx : c_int
                               ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_char),
                       c_int)
            def WpFnGeneric(hdwf, szTx, cTx) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartTx
                          )(hdwf, szTx, cTx)
                return iretVal
            return WpFnGeneric(hdwf, szTx, cTx)

        def WpDwfDigitalUartRx(self,
                               hdwf : c_int,
                               szRx : POINTER(c_char),
                               cRx : c_int,
                               pcRx : POINTER(c_int),
                               pParity : POINTER(c_int)
                               ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_char),
                       c_int, POINTER(c_int), POINTER(c_int))
            def WpFnGeneric(hdwf, szRx, cRx, pcRx, pParity) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalUartRx
                          )(hdwf, szRx, cRx, pcRx, pParity)
                return iretVal
            return WpFnGeneric(hdwf, szRx, cRx, pcRx, pParity)

        def WpDwfDigitalSpiReset(self,
                                 hdwf : c_int,
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalSpiFrequencySet(self,
                                        hdwf : c_int,
                                        hz : c_double
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, hz) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiFrequencySet
                          )(hdwf, c_double(hz))
                return iretVal
            return WpFnGeneric(hdwf, hz)

        def WpDwfDigitalSpiClockSet(self,
                                    hdwf : c_int,
                                    idxChannel : c_int
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiClockSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalSpiDataSet(self,
                                   hdwf : c_int,
                                   idxDQ : c_int,
                                   idxChannel : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int)
            def WpFnGeneric(hdwf, idxDQ, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiDataSet
                          )(hdwf, idxDQ, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxDQ, idxChannel)

        def WpDwfDigitalSpiIdleSet(self,
                                   hdwf : c_int,
                                   idxDQ : c_int,
                                   idle : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int)
            def WpFnGeneric(hdwf, idxDQ, idle) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiIdleSet
                          )(hdwf, idxDQ, idle)
                return iretVal
            return WpFnGeneric(hdwf, idxDQ, idle)

        def WpDwfDigitalSpiModeSet(self,
                                   hdwf : c_int,
                                   iMode : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, iMode) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiModeSet
                          )(hdwf, iMode)
                return iretVal
            return WpFnGeneric(hdwf, iMode)

        def WpDwfDigitalSpiOrderSet(self,
                                    hdwf : c_int,
                                    fMSBFirst : c_int
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fMSBFirst) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiOrderSet
                          )(hdwf, fMSBFirst)
                return iretVal
            return WpFnGeneric(hdwf, fMSBFirst)

        def WpDwfDigitalSpiDelaySet(self,
                                    hdwf : c_int,
                                    cStart : c_int,
                                    cCmd : c_int,
                                    cWord : c_int,
                                    cStop : c_int
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, c_int, c_int)
            def WpFnGeneric(hdwf, cStart, cCmd,
                            cWord, cStop) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiDelaySet
                          )(hdwf, cStart, cCmd,
                            cWord, cStop)
                return iretVal
            return WpFnGeneric(hdwf, cStart, cCmd,
                               cWord, cStop)

        def WpDwfDigitalSpiSelectSet(self,
                                     hdwf : c_int,
                                     idxSelect : c_int,
                                     fIdle : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int)
            def WpFnGeneric(hdwf, idxSelect, fIdle) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiSelectSet
                          )(hdwf, idxSelect, fIdle)
                return iretVal
            return WpFnGeneric(hdwf, idxSelect, fIdle)

        def WpDwfDigitalSpiSelect(self,
                                  hdwf : c_int,
                                  idxChannel : c_int,
                                  level : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int)
            def WpFnGeneric(hdwf, idxChannel, level) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiSelect
                          )(hdwf, idxChannel, level)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, level)

        def WpDwfDigitalSpiWriteRead(self,
                                     hdwf : c_int,
                                     cDQ : c_int,
                                     cBitPerWord : c_int,
                                     rgTX : POINTER(c_ubyte),
                                     cTX : c_int,
                                     rgRX : POINTER(c_ubyte),
                                     cRX : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_ubyte), c_int,
                       POINTER(c_ubyte), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiWriteRead
                          )(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord, rgTX, cTX, rgRX, cRX)

        def WpDwfDigitalSpiWriteRead16(self,
                                       hdwf : c_int,
                                       cDQ : c_int,
                                       cBitPerWord : c_int,
                                       rgTX : POINTER(c_ushort),
                                       cTX : c_int,
                                       rgRX : POINTER(c_ushort),
                                       cRX : c_int
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_ushort), c_int,
                       POINTER(c_ushort), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgTX, cTx, rgRX,
                            cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiWriteRead16
                          )(hdwf, cDQ, cBitPerWord,
                            rgTX, cTx, rgRX,
                            cRX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               rgTX, cTx, rgRX,
                               cRX)

        def WpDwfDigitalSpiWriteRead32(self,
                                       hdwf : c_int,
                                       cDQ : c_int,
                                       cBitPerWord : c_int,
                                       rgTX : POINTER(c_uint),
                                       cTX : c_int,
                                       rgRX : POINTER(c_uint),
                                       cRX : c_int
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_uint), c_int,
                       POINTER(c_uint), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiWriteRead32
                          )(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               rgTX, cTX, rgRX,
                               cRX)

        def WpDwfDigitalSpiRead(self,
                                hdwf : c_int,
                                cDQ : c_int,
                                cBitPerWord : POINTER(c_int),
                                rgRX : POINTER(c_ubyte),
                                cRX : c_int
                                ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_int), POINTER(c_ubyte), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgRX, cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiRead
                          )(hdwf, cDQ, cBitPerWord,
                            rgRX, cRX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               rgRX, cRX)

        def WpDwfDigitalSpiReadOne(self,
                                   hdwf : c_int,
                                   cDQ : c_int,
                                   cBitPerWord : c_int,
                                   pRX : POINTER(c_uint)
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            pRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiReadOne
                          )(hdwf, cDQ, cBitPerWord,
                            pRX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               pRX)

        def WpDwfDigitalSpiRead16(self,
                                  hdwf : c_int,
                                  cDQ : c_int,
                                  cBitPerWord : c_int,
                                  rgRX : POINTER(c_ushort),
                                  cRX : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_ushort), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgRX, cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiRead16
                          )(hdwf, cDQ, cBitPerWord,
                            rgRX, cRX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               rgRX, cRX)

        def WpDwfDigitalSpiRead32(self,
                                  hdwf : c_int,
                                  cDQ : c_int,
                                  cBitPerWord : c_int,
                                  rgRX : POINTER(c_uint),
                                  cRX : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_uint), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgRX, cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiRead32
                          )(hdwf, cDQ, cBitPerWord,
                            rgRX, cRX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               rgRX, cRX)

        def WpDwfDigitalSpiWrite(self,
                                 hdwf : c_int,
                                 cDQ : c_int,
                                 cBitPerWord : c_int,
                                 rgTX : POINTER(c_ubyte),
                                 cTX : c_int
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_ubyte), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiWrite
                          )(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               rgTX, cTX)

        def WpDwfDigitalSpiWriteOne(self,
                                    hdwf : c_int,
                                    cDQ : c_int,
                                    cBits : c_int,
                                    vTX : c_uint
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, c_uint)
            def WpFnGeneric(hdwf, cDQ, cBits,
                            vTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiWriteOne
                          )(hdwf, cDQ, cBits,
                            vTX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBits,
                               vTX)

        def WpDwfDigitalSpiWrite16(self,
                                   hdwf : c_int,
                                   cDQ : c_int,
                                   cBitPerWord : c_int,
                                   rgTX : POINTER(c_ushort),
                                   cTX : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_ushort), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiWrite16
                          )(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               rgTX, cTX)

        def WpDwfDigitalSpiWrite32(self,
                                   hdwf : c_int,
                                   cDQ : c_int,
                                   cBitPerWord : c_int,
                                   rgTX : POINTER(c_uint),
                                   cTX : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_uint), c_int)
            def WpFnGeneric(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiWrite32
                          )(hdwf, cDQ, cBitPerWord,
                            rgTX, cTX)
                return iretVal
            return WpFnGeneric(hdwf, cDQ, cBitPerWord,
                               rgTX, cTX)

        def WpDwfDigitalSpiCmdWriteRead(self,
                                        hdwf : c_int,
                                        cBitCmd : c_int,
                                        cmd : c_uint,
                                        cDummy : c_int,
                                        cDQ : c_int,
                                        cBitPerWord : c_int,
                                        rgTX : POINTER(c_ubyte),
                                        cTX : c_int,
                                        rgRX : POINTER(c_ubyte),
                                        cRX : c_int
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_int, c_int,
                       c_int, POINTER(c_ubyte), c_int,
                       POINTER(c_ubyte), c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWriteRead
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgTX, cTX, rgRX,
                               cRX)

        def WpDwfDigitalSpiCmdWriteRead16(self,
                                          hdwf : c_int,
                                          cBitCmd : c_int,
                                          cmd : c_uint,
                                          cDummy : c_int,
                                          cDQ : c_int,
                                          cBitPerWord : c_int,
                                          rgTX : POINTER(c_ushort),
                                          cTX : c_int,
                                          rgRX : POINTER(c_ushort),
                                          cRX : c_int
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, c_int, c_int,
                       POINTER(c_ushort), c_int, POINTER(c_ushort),
                       c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWriteRead16
                          )(hdwf, )
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgTX, cTX, rgRX,
                               cRX)

        def WpDwfDigitalSpiCmdWriteRead32(self,
                                          hdwf : c_int,
                                          cBitCmd : c_int,
                                          cmd : c_uint,
                                          cDummy : c_int,
                                          cDQ : c_int,
                                          cBitPerWord : c_int,
                                          rgTX : POINTER(c_uint),
                                          cTX : c_int,
                                          rgRX : POINTER(c_uint),
                                          cRX : c_int
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, c_int, c_int,
                       POINTER(c_ushort), c_int, POINTER(c_ushort),
                       c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWriteRead32
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX, rgRX,
                            cRX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgTX, cTX, rgRX,
                               cRX)

        def WpDwfDigitalSpiCmdRead(self,
                                   hdwf : c_int,
                                   cBitCmd : c_int,
                                   cmd : c_uint,
                                   cDummy : c_int,
                                   cDQ : c_int,
                                   cBitPerWord : c_int,
                                   rgRX : POINTER(c_ubyte),
                                   cRX : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_uint,
                       c_int, c_int, c_int,
                       POINTER(c_ubyte), c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgRX, cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdRead
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgRX, cRX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgRX, cRX)

        def WpDwfDigitalSpiCmdReadOne(self,
                                      hdwf : c_int,
                                      cBitCmd : c_int,
                                      cmd : c_uint,
                                      cDummy : c_int,
                                      cDQ : c_int,
                                      cBitPerWord : c_int,
                                      pRX : POINTER(c_uint)
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_int, c_int,
                       c_int, POINTER(c_uint))
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            pRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdReadOne
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            pRX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               pRX)

        def WpDwfDigitalSpiCmdRead16(self,
                                     hdwf : c_int,
                                     cBitCmd : c_int,
                                     cmd : c_uint,
                                     cDummy : c_int,
                                     cDQ : c_int,
                                     cBitPerWord : c_int,
                                     rgRX : POINTER(c_ushort),
                                     cRX : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_int, c_int,
                       c_int, POINTER(c_ushort), c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgRX, cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdRead16
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgRX, cRX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgRX, cRX)

        def WpDwfDigitalSpiCmdRead32(self,
                                     hdwf : c_int,
                                     cBitCmd : c_int,
                                     cmd : c_uint,
                                     cDummy : c_int,
                                     cDQ : c_int,
                                     cBitPerWord : c_int,
                                     rgRX : POINTER(c_uint),
                                     cRX : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_int, c_int,
                       c_int, POINTER(c_uint), c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgRX, cRX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdRead32
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgRX, cRX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgRX, cRX)

        def WpDwfDigitalSpiCmdWrite(self,
                                    hdwf : c_int,
                                    cBitCmd : c_int,
                                    cmd : c_uint,
                                    cDummy : c_int,
                                    cDQ : c_int,
                                    cBitPerWord : c_int,
                                    rgTX : POINTER(c_ubyte),
                                    cTX : c_int
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_int, c_int,
                       c_int, POINTER(c_ubyte), c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWrite
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgTX, cTX)

        def WpDwfDigitalSpiCmdWriteOne(self,
                                       hdwf : c_int,
                                       cBitCmd : c_int,
                                       cmd : c_uint,
                                       cDummy : c_int,
                                       cDQ : c_int,
                                       cBits : c_int,
                                       vTX : c_uint
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_int, c_int,
                       c_int, c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBits,
                            vTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWriteOne
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBits,
                            vTX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBits,
                               vTX)

        def WpDwfDigitalSpiCmdWrite16(self,
                                      hdwf : c_int,
                                      cBitCmd : c_int,
                                      cmd : c_uint,
                                      cDummy : c_int,
                                      cDQ : c_int,
                                      cBitPerWord : c_int,
                                      rgTX : POINTER(c_ushort),
                                      cTX : c_int
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_int, c_int,
                       c_int, POINTER(c_ushort), c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWrite16
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgTX, cTX)

        def WpDwfDigitalSpiCmdWrite32(self,
                                      hdwf : c_int,
                                      cBitCmd : c_int,
                                      cmd : c_uint,
                                      cDummy : c_int,
                                      cDQ : c_int,
                                      cBitPerWord : c_int,
                                      rgTX : POINTER(c_uint),
                                      cTX : c_int
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_uint, c_int, c_int,
                       c_int, POINTER(c_uint), c_int)
            def WpFnGeneric(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSpiCmdWrite32
                          )(hdwf, cBitCmd, cmd,
                            cDummy, cDQ, cBitPerWord,
                            rgTX, cTX)
                return iretVal
            return WpFnGeneric(hdwf, cBitCmd, cmd,
                               cDummy, cDQ, cBitPerWord,
                               rgTX, cTX)

        def WpDwfDigitalI2cReset(self,
                                 hdwf : c_int,
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalI2cClear(self,
                                 hdwf : c_int,
                                 pfFree : POINTER(c_int)
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfFree) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cClear
                          )(hdwf, pfFree)
                return iretVal
            return WpFnGeneric(hdwf, pfFree)

        def WpDwfDigitalI2cStretchSet(self,
                                      hdwf : c_int,
                                      fEnable : c_int
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fEnable) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cStretchSet
                          )(hdwf, fEnable)
                return iretVal
            return WpFnGeneric(hdwf, fEnable)

        def WpDwfDigitalI2cRateSet(self,
                                   hdwf : c_int,
                                   hz : c_double
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, hz) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cRateSet
                          )(hdwf, c_double(hz))
                return iretVal
            return WpFnGeneric(hdwf, hz)

        def WpDwfDigitalI2cReadNakSet(self,
                                      hdwf : c_int,
                                      fNakLastReadByte : c_int
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fNakLastReadByte) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cReadNakSet
                          )(hdwf, fNakLastReadByte)
                return iretVal
            return WpFnGeneric(hdwf, fNakLastReadByte)

        def WpDwfDigitalI2cSclSet(self,
                                  hdwf : c_int,
                                  idxChannel : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cSclSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalI2cSdaSet(self,
                                  hdwf : c_int,
                                  idxChannel : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cSdaSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalI2cTimeoutSet(self,
                                      hdwf : c_int,
                                      sec : c_double
                                      ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, sec) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cTimeoutSet
                          )(hdwf, c_double(sec))
                return iretVal
            return WpFnGeneric(hdwf, sec)

        def WpDwfDigitalI2cWriteRead(self,
                                     hdwf : c_int,
                                     adr8bits : c_ubyte,
                                     rgbTx : POINTER(c_ubyte),
                                     cTx : c_int,
                                     rgRx : POINTER(c_ubyte),
                                     cRx : c_int,
                                     pNak : POINTER(c_int)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ubyte,
                       POINTER(c_ubyte), c_int, POINTER(c_ubyte),
                       c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, adr8bits, rgbTx,
                            cTx, rgRx, cRx,
                            pNak) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cWriteRead
                          )(hdwf, adr8bits, rgbTx,
                            cTx, rgRx, cRx,
                            pNak)
                return iretVal
            return WpFnGeneric(hdwf, adr8bits, rgbTx,
                               cTx, rgRx, cRx,
                               pNak)

        def WpDwfDigitalI2cRead(self,
                                hdwf : c_int,
                                adr8bits : c_ubyte,
                                rgbRx : POINTER(c_ubyte),
                                cRx : c_int,
                                pNak : POINTER(c_int)
                                ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ubyte,
                       POINTER(c_ubyte), c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, adr8bits, rgbRx,
                            cRx, pNak) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cRead
                          )(hdwf, adr8bits, rgbRx,
                            cRx, pNak)
                return iretVal
            return WpFnGeneric(hdwf, adr8bits, rgbRx,
                               cRx, pNak)

        def WpDwfDigitalI2cWrite(self,
                                 hdwf : c_int,
                                 adr8bits : c_ubyte,
                                 rgbTx : POINTER(c_ubyte),
                                 cTx : c_int,
                                 pNak : POINTER(c_int)
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ubyte,
                       POINTER(c_ubyte), c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, adr8bits, rgbTx,
                            cTx, pNak) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cWrite
                          )(hdwf, adr8bits, rgbTx,
                            cTx, pNak)
                return iretVal
            return WpFnGeneric(hdwf, adr8bits, rgbTx,
                               cTx, pNak)

        def WpDwfDigitalI2cWriteOne(self,
                                    hdwf : c_int,
                                    adr8bits : c_ubyte,
                                    bTx : c_ubyte,
                                    pNak : POINTER(c_int)
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_ubyte,
                       POINTER(c_int))
            def WpFnGeneric(hdwf, adr8bits, bTx,
                            pNak) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cWriteOne
                          )(hdwf, adr8bits, bTx,
                            pNak)
                return iretVal
            return WpFnGeneric(hdwf, adr8bits, bTx,
                               pNak)

        def WpDwfDigitalI2cSpyStart(self,
                                    hdwf : c_int,
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cSpyStart
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalI2cSpyStatus(self,
                                     hdwf : c_int,
                                     fStart : POINTER(c_int),
                                     fStop : POINTER(c_int),
                                     rgData : POINTER(c_ubyte),
                                     cData : POINTER(c_int),
                                     iNak : POINTER(c_int)
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int),
                       POINTER(c_int), POINTER(c_ubyte), POINTER(c_int),
                       POINTER(c_int))
            def WpFnGeneric(hdwf, fStart, fStop,
                            rgData, cData, iNak) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalI2cSpyStatus
                          )(hdwf, fStart, fStop,
                            rgData, cData, iNak)
                return iretVal
            return WpFnGeneric(hdwf, fStart, fStop,
                               rgData, cData, iNak)

        def WpDwfDigitalCanReset(self,
                                 hdwf : c_int,
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalCanReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalCanRateSet(self,
                                   hdwf : c_int,
                                   hz : c_double
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, hz) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwf
                          )(hdwf, c_double(hz))
                return iretVal
            return WpFnGeneric(hdwf, hz)

        def WpDwfDigitalCanPolaritySet(self,
                                       hdwf : c_int,
                                       fHigh : c_int
                                       ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fHigh) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalCanPolaritySet
                          )(hdwf, fHigh)
                return iretVal
            return WpFnGeneric(hdwf, fHigh)

        def WpDwfDigitalCanTxSet(self,
                                 hdwf : c_int,
                                 idxChannel : c_int
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalCanTxSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalCanRxSet(self,
                                 hdwf : c_int,
                                 idxChannel : c_int
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalCanRxSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalCanTx(self,
                              hdwf : c_int,
                              vID : c_int,
                              fExtended : c_int,
                              fRemote : c_int,
                              cDLC : c_int,
                              rgTX : POINTER(c_ubyte)
                              ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, c_int, c_int,
                       POINTER(c_ubyte))
            def WpFnGeneric(hdwf, vID, fExtended,
                            fRemote, cDLC, rgTX) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalCanTx
                          )(hdwf, vID, fExtended,
                            fRemote, cDLC, rgTX)
                return iretVal
            return WpFnGeneric(hdwf, vID, fExtended,
                               fRemote, cDLC, rgTX)

        def WpDwfDigitalCanRx(self,
                              hdwf : c_int,
                              pvID : POINTER(c_int),
                              pfExtended : POINTER(c_int),
                              pfRemote : POINTER(c_int),
                              pcDLC : POINTER(c_int),
                              rgRX : POINTER(c_ubyte),
                              cRX : c_int,
                              pvStatus : POINTER(c_int)
                              ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int),
                       POINTER(c_int), POINTER(c_int), POINTER(c_int),
                       POINTER(c_ubyte), c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pvID, pfExtended,
                            pfRemote, pcDLC, rgRX,
                            cRX, pvStatus) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalCanRx
                          )(hdwf, pvID, pfExtended,
                            pfRemote, pcDLC, rgRX,
                            cRX, pvStatus)
                return iretVal
            return WpFnGeneric(hdwf, pvID, pfExtended,
                               pfRemote, pcDLC, rgRX,
                               cRX, pvStatus)

        def WpDwfDigitalSwdReset(self,
                                 hdwf : c_int,
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfDigitalSwdRateSet(self,
                                   hdwf : c_int,
                                   hz : c_double
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_double)
            def WpFnGeneric(hdwf, hz) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdRateSet
                          )(hdwf, c_double(hz))
                return iretVal
            return WpFnGeneric(hdwf, hz)

        def WpDwfDigitalSwdCkSet(self,
                                 hdwf : c_int,
                                 idxChannel : c_int
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdCkSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalSwdIoSet(self,
                                 hdwf : c_int,
                                 idxChannel : c_int
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdIoSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfDigitalSwdTurnSet(self,
                                   hdwf : c_int,
                                   cTurn : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, cTurn) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdTurnSet
                          )(hdwf, cTurn)
                return iretVal
            return WpFnGeneric(hdwf, cTurn)

        def WpDwfDigitalSwdTrailSet(self,
                                    hdwf : c_int,
                                    cTrail : c_int
                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, cTrail) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdTrailSet
                          )(hdwf, cTrail)
                return iretVal
            return WpFnGeneric(hdwf, cTrail)

        def WpDwfDigitalSwdParkSet(self,
                                   hdwf : c_int,
                                   fDrive : c_int
                                   ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fDrive) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdParkSet
                          )(hdwf, fDrive)
                return iretVal
            return WpFnGeneric(hdwf, fDrive)

        def WpDwfDigitalSwdNakSet(self,
                                  hdwf : c_int,
                                  fContinue : c_int
                                  ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fContinue) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdNakSet
                          )(hdwf, fContinue)
                return iretVal
            return WpFnGeneric(hdwf, fContinue)

        def WpDwfDigitalSwdIoIdleSet(self,
                                     hdwf : c_int,
                                     fHigh : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int)
            def WpFnGeneric(hdwf, fHigh) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdIoIdleSet
                          )(hdwf, fHigh)
                return iretVal
            return WpFnGeneric(hdwf, fHigh)

        def WpDwfDigitalSwdClear(self,
                                 hdwf : c_int,
                                 cReset : c_int,
                                 cTrail : c_int
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int, c_int)
            def WpFnGeneric(hdwf, cRepeat, cTrail) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdClear
                          )(hdwf, cRepeat, cTrail)
                return iretVal
            return WpFnGeneric(hdwf, cRepeat, cTrail)

        def WpDwfDigitalSwdWrite(self,
                                 hdwf : c_int,
                                 APnDP : c_int,
                                 A32 : c_int,
                                 pAck : POINTER(c_int),
                                 Write : c_uint
                                 ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_int), c_uint)
            def WpFnGeneric(hdwf, APnDP, A32, pAck, Write) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdWrite
                          )(hdwf, hdwf, APnDP, A32, pAck, Write)
                return iretVal
            return WpFnGeneric(hdwf, hdwf, APnDP, A32, pAck, Write)

        def WpDwfDigitalSwdRead(self,
                                hdwf : c_int,
                                APnDP : c_int,
                                A32 : c_int,
                                pAck : POINTER(c_int),
                                pRead : POINTER(c_uint),
                                pCrc : POINTER(c_int)
                                ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, POINTER(c_int), POINTER(c_int),
                       POINTER(c_int))
            def WpFnGeneric(hdwf, APnDP, A32,
                            pAck, pRead, pCrc) -> int:
                iretVal = self.dtFuncDP.get(
                            DwfFuncCorrelationDigital.cFDwfDigitalSwdRead
                          )(hdwf, APnDP, A32,
                            pAck, pRead, pCrc)
                return iretVal
            return WpFnGeneric(hdwf, APnDP, A32,
                               pAck, pRead, pCrc)

        def cntrlDigitalUart(self,
                             dUart : dict,
                             bSet : bool
                             ) -> int:
            """
            @Description
            Uart options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dRepetition : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Uart control.
            bSet : Flag for setter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dUart.keys())
            if not ("Reset" in lsKeys or
                    "Rate" in lsKeys or
                    "Bits" in lsKeys or
                    "Parity" in lsKeys or
                    "Polarity" in lsKeys or
                    "Stop" in lsKeys or
                    "Tx" in lsKeys or
                    "Rx" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dUart["Reset"]:
                iRet = self.WpDwfDigitalUartReset(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dUart["Reset"] = False
            
            if dUart["Rate"] and bSet:
                iRet = self.WpDwfDigitalUartRateSet(
                            self.iHnd,
                            self.hz
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dUart["Rate"] = False
            
            if dUart["Bits"] and bSet:
                iRet = self.WpDwfDigitalUartBitsSet(
                            self.iHnd,
                            self.cBits
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dUart["Bits"] = False
            
            if dUart["Parity"] and bSet:
                iRet = self.WpDwfDigitalUartParitySet(
                            self.iHnd,
                            self.parity
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dUart["Parity"] = False
            
            if dUart["Polarity"] and bSet:
                iRet = self.WpDwfDigitalUartPolaritySet(
                            self.iHnd,
                            self.polarity
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dUart["Polarity"] = False
            
            if dUart["Stop"] and bSet:
                iRet = self.WpDwfDigitalUartStopSet(
                            self.iHnd,
                            self.cBit
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dUart["Stop"] = False
            
            if dUart["Tx"]:
                if bSet:
                    iRet = self.WpDwfDigitalUartTxSet(
                                self.iHnd,
                                self.idxChannel
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                else:
                    iRet = self.WpDwfDigitalUartTx(
                                self.iHnd,
                                self.szTx,
                                self.cTX
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dUart["Tx"] = False
            
            if dUart["Rx"]:
                if bSet:
                    iRet = self.WpDwfDigitalUartRxSet(
                                self.iHnd,
                                self.idxChannel
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                else:
                    iRet = self.WpDwfDigitalUartRx(
                                self.iHnd,
                                self.szRx,
                                self.retCRx,
                                self.retParity
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dUart["Rx"] = False
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalSpi(self,
                            dSpi : dict,
                            bSet : bool
                            ) -> int:
            """
            @Description
            Uart options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dRepetition : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Uart control.
            bSet : Flag for setter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dSpi.keys())
            if not ("Reset" in lsKeys or
                    "Frequency" in lsKeys or
                    "Clock" in lsKeys or
                    "Data" in lsKeys or
                    "Idle" in lsKeys or
                    "Mode" in lsKeys or
                    "Order" in lsKeys or
                    "Delay" in lsKeys or
                    "Select" in lsKeys or
                    "Write" in lsKeys or
                    "Read" in lsKeys or
                    "Write" in lsKeys or
                    "WriteRead" in lsKeys or
                    "WriteRead16" in lsKeys or
                    "WriteRead32" in lsKeys or
                    "ReadOne" in lsKeys or
                    "Read16" in lsKeys or
                    "Read32" in lsKeys or
                    "WriteOne" in lsKeys or
                    "CmdWriteRead" in lsKeys or
                    "CmdWrite16" in lsKeys or
                    "CmdWrite32" in lsKeys or
                    "CmdRead" in lsKeys or
                    "CmdReadOne" in lsKeys or
                    "CmdRead16" in lsKeys or
                    "CmdRead32" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dSpi["Reset"]:
                iRet = self.WpDwfDigitalSpiReset(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Reset"] = False
            
            if dSpi["Frequency"]:
                iRet = self.WpDwfDigitalSpiFrequencySet(
                            self.iHnd,
                            self.hz
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Frequency"] = False
            
            if dSpi["Clock"] and bSet:
                iRet = self.WpDwfDigitalSpiClockSet(
                            self.iHnd,
                            self.idxChannel
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Clock"] = False
            
            if dSpi["Data"] and bSet:
                iRet = self.WpDwfDigitalSpiDataSet(
                            self.iHnd,
                            self.idxDQ,
                            self.idxChannel
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Data"] = False
            
            if dSpi["Idle"] and bSet:
                iRet = self.WpDwfDigitalSpiIdleSet(
                            self.iHnd,
                            self.idxDQ,
                            self.idle
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Idle"] = False
            
            if dSpi["Mode"] and bSet:
                iRet = self.WpDwfDigitalSpiModeSet(
                            self.iHnd,
                            self.iMode
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Mode"] = False
            
            if dSpi["Order"] and bSet:
                iRet = self.WpDwfDigitalSpiOrderSet(
                            self.iHnd,
                            self.fMSBFirst
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Order"] = False
            
            if dSpi["Delay"] and bSet:
                iRet = self.WpDwfDigitalSpiDelaySet(
                            self.iHnd,
                            self.cStart,
                            self.cCmd,
                            self.cWord,
                            self.cStop
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Delay"] = False
            
            if dSpi["Select"]:
                if bSet:
                    iRet = self.WpDwfDigitalSpiSelect(
                                self.iHnd,
                                self.idxChannel,
                                self.level
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                else:
                    iRet = self.WpDwfDigitalSpiSelectSet(
                                self.iHnd,
                                self.idxChannel,
                                self.fIdle
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dSpi["Select"] = False
            
            if dSpi["WriteRead"]:
                iRet = self.WpDwfDigitalSpiWriteRead(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.ucRgTX,
                            self.cTx,
                            self.ucRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["WriteRead"] = False
            
            if dSpi["WriteRead16"]:
                iRet = self.WpDwfDigitalSpiWriteRead16(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.usRgTX,
                            self.cTx,
                            self.usRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["WriteRead16"] = False
            
            if dSpi["WriteRead32"]:
                iRet = self.WpDwfDigitalSpiWriteRead32(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.uiRgTX,
                            self.cTx,
                            self.uiRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["WriteRead32"] = False
            
            if dSpi["Read"]:
                iRet = self.WpDwfDigitalSpiRead(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.ucRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Read"] = False
            
            if dSpi["ReadOne"]:
                iRet = self.WpDwfDigitalSpiReadOne(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.uipRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["ReadOne"] = False
            
            if dSpi["Read16"]:
                iRet = self.WpDwfDigitalSpiRead16(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.usRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Read16"] = False
            
            if dSpi["Read32"]:
                iRet = self.WpDwfDigitalSpiRead32(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.uiRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Read32"] = False
            
            if dSpi["Write"]:
                iRet = self.WpDwfDigitalSpiWrite(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.ucRgTX,
                            self.cTX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Write"] = False
            
            if dSpi["WriteOne"]:
                iRet = self.WpDwfDigitalSpiWriteOne(
                            self.iHnd,
                            self.cDQ,
                            self.cBits,
                            self.vTX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["WriteOne"] = False
            
            if dSpi["Write16"]:
                iRet = self.WpDwfDigitalSpiWrite16(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.usRgTX,
                            self.cTX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Write16"] = False
            
            if dSpi["Write32"]:
                iRet = self.WpDwfDigitalSpiWrite32(
                            self.iHnd,
                            self.cDQ,
                            self.cBitPerWord,
                            self.uiRgTX,
                            self.cTX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["Write32"] = False
            
            if dSpi["CmdWriteRead"]:
                iRet = self.WpDwfDigitalSpiCmdWriteRead(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBitPerWord,
                            self.ucRgTX,
                            self.cTX,
                            self.ucRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdWriteRead"] = False
            
            if dSpi["CmdWrite16"]:
                iRet = self.WpDwfDigitalSpiCmdWrite16(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBitPerWord,
                            self.usRgTX,
                            self.cTX,
                            self.usRgRX,
                            self.cRX                            
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdWrite16"] = False
            
            if dSpi["CmdWrite32"]:
                iRet = self.WpDwfDigitalSpiCmdWrite32(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBitPerWord,
                            self.uiRgTX,
                            self.cTX,
                            self.uiRgRX,
                            self.cRX                            
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdWrite32"] = False
            
            if dSpi["CmdWrite"]:
                iRet = self.WpDwfDigitalSpiCmdWrite(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBitPerWord,
                            self.ucRgTX,
                            self.cTX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdWrite"] = False
            
            if dSpi["CmdWriteOne"]:
                iRet = self.WpDwfDigitalSpiCmdWriteOne(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBits,
                            self.vTX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdWriteOne"] = False
            
            if dSpi["CmdRead"]:
                iRet = self.WpDwfDigitalSpiCmdRead(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBitPerWord,
                            self.ucRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdRead"] = False
            
            if dSpi["CmdReadOne"]:
                iRet = self.WpDwfDigitalSpiCmdReadOne(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBitPerWord,
                            self.uipRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdReadOne"] = False
            
            if dSpi["CmdRead16"]:
                iRet = self.WpDwfDigitalSpiCmdRead16(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBitPerWord,
                            self.usRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdRead16"] = False
            
            if dSpi["CmdRead32"]:
                iRet = self.WpDwfDigitalSpiCmdRead32(
                            self.iHnd,
                            self.cBitCmd,
                            self.cmd,
                            self.cDummy,
                            self.cDQ,
                            self.cBitPerWord,
                            self.uiRgRX,
                            self.cRX
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSpi["CmdRead32"] = False
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalI2c(self,
                            dI2c : dict,
                            bSet : bool
                            ) -> int:
            """
            @Description
            I2c options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dRepetition : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain I2c control.
            bSet : Flag for setter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dI2c.keys())
            if not ("Reset" in lsKeys or
                    "Clear" in lsKeys or
                    "Stretch" in lsKeys or
                    "Rate" in lsKeys or
                    "Scl" in lsKeys or
                    "Sda" in lsKeys or
                    "Timeout" in lsKeys or
                    "WriteRead" in lsKeys or
                    "Read" in lsKeys or
                    "Write" in lsKeys or
                    "WriteOne" in lsKeys or
                    "SpyStart" in lsKeys or
                    "SpyStatus" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dI2c["Reset"]:
                iRet = self.WpDwfDigitalI2cReset(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Reset"] = False
            
            if dI2c["Clear"]:
                iRet = self.WpDwfDigitalI2cClear(
                            self.iHnd,
                            self.retFFree
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Clear"] = False
            
            if dI2c["Stretch"] and bSet:
                iRet = self.WpDwfDigitalI2cStretchSet(
                            self.iHnd,
                            self.fEnable
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Stretch"] = False
            
            if dI2c["Rate"] and bSet:
                iRet = self.WpDwfDigitalI2cRateSet(
                            self.iHnd,
                            self.hz
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Rate"] = False
            
            if dI2c["ReadNak"] and bSet:
                iRet = self.WpDwfDigitalI2cReadNakSet(
                            self.iHnd,
                            self.fNakLastReadByte
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["ReadNak"] = False
            
            if dI2c["Scl"] and bSet:
                iRet = self.WpDwfDigitalI2cSclSet(
                            self.iHnd,
                            self.idxChannel
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Scl"] = False
            
            if dI2c["Sda"] and bSet:
                iRet = self.WpDwfDigitalI2cSdaSet(
                            self.iHnd,
                            self.idxChannel
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Sda"] = False
            
            if dI2c["Timeout"] and bSet:
                iRet = self.WpDwfDigitalI2cTimeoutSet(
                            self.iHnd,
                            self.sec
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Timeout"] = False
            
            if dI2c["WriteRead"]:
                iRet = self.WpDwfDigitalI2cWriteRead(
                            self.iHnd,
                            self.adr8bits,
                            self.ucRgbTx,
                            self.cTx,
                            self.ucRgRx,
                            self.cRx,
                            self.retNak
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["WriteRead"] = False
            
            if dI2c["Read"]:
                iRet = self.WpDwfDigitalI2cRead(
                            self.iHnd,
                            self.adr8bits,
                            self.ucRgbRx,
                            self.cRx,
                            self.retNak
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Read"] = False
            
            if dI2c["Write"]:
                iRet = self.WpDwfDigitalI2cWrite(
                            self.iHnd,
                            self.adr8bits,
                            self.ucRgbTx,
                            self.cTx,
                            self.retNak
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["Write"] = False
            
            if dI2c["WriteOne"]:
                iRet = self.WpDwfDigitalI2cWriteOne(
                            self.iHnd,
                            self.adr8bits,
                            self.bTx,
                            self.retNak
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["WriteOne"] = False
            
            if dI2c["SpyStart"]:
                iRet = self.WpDwfDigitalI2cSpyStart(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["SpyStart"] = False
            
            if dI2c["SpyStatus"]:
                iRet = self.WpDwfDigitalI2cSpyStatus(
                            self.iHnd,
                            self.retFStart,
                            self.retFStop,
                            self.ucRgData,
                            self.cData,
                            self.retINak
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dI2c["SpyStatus"] = False
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalCan(self,
                            dCan : dict,
                            bSet : bool
                            ) -> int:
            """
            @Description
            Can options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dRepetition : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Can control.
            bSet : Flag for setter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dCan.keys())
            if not ("Reset" in lsKeys or
                    "Rate" in lsKeys or
                    "Polarity" in lsKeys or
                    "Tx" in lsKeys or
                    "Rx" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dCan["Reset"]:
                iRet = self.WpDwfDigitalCanReset(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dCan["Reset"] = False
            
            if dCan["Rate"] and bSet:
                iRet = self.WpDwfDigitalCanRateSet(
                            self.iHnd,
                            self.hz
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dCan["Rate"] = False
            
            if dCan["Polarity"] and bSet:
                iRet = self.WpDwfDigitalCanPolaritySet(
                            self.iHnd,
                            self.fHigh
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dCan["Polarity"] = False
            
            if dCan["Tx"]:
                if bSet:
                    iRet = self.WpDwfDigitalCanTxSet(
                                self.iHnd,
                                self.idxChannel
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                else:
                    iRet = self.WpDwfDigitalCanTx(
                                self.iHnd,
                                self.vID,
                                self.fExtended,
                                self.fRemote,
                                self.cDLC,
                                self.rgTX
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dCan["Tx"] = False
            
            if dCan["Rx"]:
                if bSet:
                    iRet = self.WpDwfDigitalCanRxSet(
                                self.iHnd,
                                self.idxChannel
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                
                else:
                    iRet = self.WpDwfDigitalCanRx(
                                self.iHnd,
                                self.retVID,
                                self.retFExtended,
                                self.retFRemote,
                                self.retCDLC,
                                self.rgRX,
                                self.cRX,
                                self.retVStatus
                                )
                    if iRet & MASK == wdsc.WP_DWFERROR:
                        return DigitalInstruments.FAILURE
                dCan["Rx"] = False
            
            return DigitalInstruments.SUCCESS

        def cntrlDigitalSwd(self,
                            dSwd : dict,
                            bSet : bool
                            ) -> int:
            """
            @Description
            Swd options for digital in instrument can be controlled
            here, but aditional functionality will be implemented into
            separated functions tha will be used from settingsinstruments.py.
            @Parameters
            dRepetition : This dictionary holds True/False values
            to switch a certain branch to call Wp... function(s)
            associated to a certain Swd control.
            bSet : Flag for setter functions.
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            Some other logic can be inserted through these "if" branches
            to analyze data from a specific board.
            """
            iRet = 0
            MASK = 0x01
            lsKeys = list(dSwd.keys())
            if not ("Reset" in lsKeys or
                    "Rate" in lsKeys or
                    "Ck" in lsKeys or
                    "Io" in lsKeys or
                    "Trun" in lsKeys or
                    "Trail" in lsKeys or
                    "Park" in lsKeys or
                    "Nak" in lsKeys or
                    "IoIdle" in lsKeys or
                    "Clear" in lsKeys or
                    "Write" in lsKeys or
                    "Read" in lsKeys
                    ):
                return DigitalInstruments.FAILURE
            
            if dSwd["Reset"]:
                iRet = self.WpDwfDigitalSwdReset(
                            self.iHnd
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Reset"] = False
            
            if dSwd["Rate"] and bSet:
                iRet = self.WpDwfDigitalSwdRateSet(
                            self.iHnd,
                            self.hz
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Reset"] = False
            
            if dSwd["Ck"] and bSet:
                iRet = self.WpDwfDigitalSwdCkSet(
                            self.iHnd,
                            self.idxChannel
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Ck"] = False
            
            if dSwd["Io"] and bSet:
                iRet = self.WpDwfDigitalSwdIoSet(
                            self.iHnd,
                            self.idxChannel
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Io"] = False
            
            if dSwd["Turn"] and bSet:
                iRet = self.WpDwfDigitalSwdTurnSet(
                            self.iHnd,
                            self.cTurn
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Turn"] = False
            
            if dSwd["Trail"] and bSet:
                iRet = self.WpDwfDigitalSwdTrailSet(
                            self.iHnd,
                            self.cTrail
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Trail"] = False
            
            if dSwd["Park"] and bSet:
                iRet = self.WpDwfDigitalSwdParkSet(
                            self.iHnd,
                            self.fDrive
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Park"] = False
            
            if dSwd["Nak"] and bSet:
                iRet = self.WpDwfDigitalSwdNakSet(
                            self.iHnd,
                            self.fContinue
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Nak"] = False
            
            if dSwd["IoIdle"] and bSet:
                iRet = self.WpDwfDigitalSwdIoIdleSet(
                            self.iHnd,
                            self.fHigh
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["IoIdle"] = False
            
            if dSwd["Clear"]:
                iRet = self.WpDwfDigitalSwdClear(
                            self.iHnd,
                            self.cRepeat,
                            self.cTrail
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Clear"] = False
            
            if dSwd["Write"]:
                iRet = self.WpDwfDigitalSwdWrite(
                            self.iHnd,
                            self.APnDP,
                            self.A32,
                            self.retAck,
                            self.Write
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Write"] = False
            
            if dSwd["Read"]:
                iRet = self.WpDwfDigitalSwdRead(
                            self.iHnd,
                            self.APnDP,
                            self.A32,
                            self.retAck,
                            self.retRead,
                            self.retCrc
                            )
                if iRet & MASK == wdsc.WP_DWFERROR:
                    return DigitalInstruments.FAILURE
                dSwd["Read"] = False
            
            return DigitalInstruments.SUCCESS

        def Uart(self,
                 bReset=False,
                 frequency=0.0,
                 bRead=False,
                 bWrite=False,
                 chDIOTx=None,
                 chDIORx=None,
                 nrCntTx=1,
                 data={"Polarity":0,"Parity":0,"BufferTx":[],
                       "BufferRx":[],"CntRx":0}
                 ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            """
            try:
                iRet = 0
                # reset, freq(hz)
                self.auxUart["Reset"] = bReset
                if frequency >= 0.0:
                    self.auxUart["Rate"] = True
                    self.hz = c_double(frequency)
                else:
                    raise ErrorWpFnGenericInstrument("Uart error: Negative frequency")
                iRet = self.cntrlDigitalUart(dUart=self.auxUart, bSet=True)
                if ((chDIOTx is not None and chDIORx is not None) and
                    (chDIOTx <= 15 and chDIOTx >= 0) and
                    (chDIORx <= 15 and chDIORx >= 0)
                    ):
                    # Tx dio
                    self.idxChannel = c_int(chDIOTx)
                    self.auxUart["Tx"] = True
                    iRet = self.cntrlDigitalUart(dUart=self.auxUart, bSet=True)
                    # Rx dio
                    self.idxChannel = c_int(chDIORx)
                    self.auxUart["Rx"] = True
                    iRet = self.cntrlDigitalUart(dUart=self.auxUart, bSet=True)
                else:
                    raise ErrorWpFnGenericInstrument("Uart error: Tx and Rx channels not set")
                # polarity, parity
                self.polarity = c_int(data["Polarity"])
                self.parity = c_int(data["Parity"])
                self.auxUart["Polarity"] = True
                self.auxUart["Parity"] = True
                iRet = self.cntrlDigitalUart(dUart=self.auxUart, bSet=True)
                if bWrite:
                    # TX, Bits, Bit ~ not yet used, TX
                    lsLoc = (c_char*len(data["BufferTx"]))()
                    for x in range(0, len(lsLoc)):
                        lsLoc[x] = c_char(data["BufferTx"][x])
                    self.szTX = lsLoc
                    self.cTX = c_int(nrCntTx)
                    self.cBits = c_int(8)
                    self.auxUart["Tx"] = True
                    iRet = self.cntrlDigitalUart(dUart=self.auxUart, bSet=False)
                if bRead:
                    # Rx, cRX , Parity
                    lsLoc = (c_char*len(data["BufferRx"]))()
                    for x in range(0, len(lsLoc)):
                        lsLoc[x] = c_char(data["BufferRx"][x])
                    self.szRx = lsLoc
                    self.auxUart["Rx"] = True
                    iRet = self.cntrlDigitalUart(dUart=self.auxUart, bSet=False)
                    data["CntRx"] = self.retCRX
                    data["Parity"] = self.retParity
            except ErrorWpFnGenericInstrument as err:
                print(err)

        def Spi(self,
                bReset=False,
                frequency=0.0,
                chDIOClock=None,
                chDIOData=None,
                chDIOCS=None,
                csIdle=0, # 0,1
                dataMode=0, # 0,1,2,3
                format=8, # 8,16,32
                bRead=False,
                nrCnt=1,
                bWrite=False,
                idle=None, # 0,1,2,3
                data={"Cmd":0,"BufferTx":[],"BufferRx":[],
                      "Mode":0,"Delay":0.0,"MSBFirst":1}
                ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            """
            try:
                # reset, freq(hz)
                self.auxSpi["Reset"] = bReset
                if frequency >= 0.0:
                    self.auxSpi["Rate"] = True
                    self.hz = c_double(frequency)
                else:
                    raise ErrorWpFnGenericInstrument("Spi error: Negative frequency")
                iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=True)
                # clock, data and cs idx
                if ((chDIOClock is not None and chDIOData is not None and
                     chDIOCS is not None) and
                     ((chDIOClock <= 15 and chDIOClock >= 0) and
                      (chDIOData <= 15 and chDIOData >= 0) and
                      (chDIOCS <= 15 and chDIOCS >= 0))
                    ):
                    self.idxChannel = c_int(chDIOClock)
                    self.auxSpi["Clock"] = True
                    iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    self.idxChannel = c_int(chDIOData)
                    self.idxDQ = c_int(dataMode)
                    self.auxSpi["Data"] = True
                    iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    self.auxSpi["Select"] = True
                    self.idxSelect = c_int(chDIOCS)
                    self.fIdle = c_int(csIdle)
                    iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=True)
                else:
                    raise ErrorWpFnGenericInstrument("Spi error: Ck, Data, CS channels not set")
                # idle
                if (idle == 0 or idle == 1 or idle == 2 or idle == 3):
                    self.auxSpi["Idle"] = True
                    self.idle = c_int(idle)
                    iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=True)
                # mode
                if data["Mode"] == 0x01 or data["Mode"] == 0x02:
                    self.auxSpi["Mode"] = True
                    self.iMode = c_int(data["Mode"])
                    iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=True)
                # order
                if data["MSBFirst"] == 0x00 or data["MSBFirst"] == 0x01:
                    self.auxSpi["Order"] = True
                    self.fMSBFirst = c_int(data["MSBFirst"])
                    iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=True)
                # delay
                if data["Delay"] > 0.0:
                    self.auxSpi["Delay"] = True
                    # delay = f(freq, cStart, cCmd, cWord, cStop)
                    _KHZ = 1e3
                    _MHZ = 1e6
                    bIsKhz = self.hz.value / _MHZ <= 1.0 if True else False
                    cntInit = bIsKhz if data["Delay"] * _KHZ else data["Delay"] * _KHZ
                    self.cStart = c_int(0)
                    self.cCmd = c_int(cntInit)
                    self.cWord = c_int(cntInit)
                    self.cStop = c_int(cntInit)
                    iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=True)
                # format for data, write/read op
                if bRead:
                    # default values, might be changed (computed differently)
                    self.cDQ = c_int(1)
                    self.cBitPerWord = c_int(16)
                    self.cRX = c_int(nrCnt)
                    if format == 8:
                        self.auxSpi["Read"] = True
                        self.ucRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 16:
                        self.auxSpi["Read16"] = True
                        self.usRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 32:
                        if nrCnt == 1:
                            self.auxSpi["ReadOne"] = True
                            self.pRX = data["BufferRx"]
                        else:
                            self.auxSpi["Read32"] = True
                            self.uiRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                
                if bWrite:
                    # default values, might be changed (computed differently)
                    self.cDQ = c_int(1)
                    self.cBitPerWord = c_int(16)
                    self.cTX = c_int(nrCnt)
                    if format == 8:
                        self.auxSpi["Write"] = True
                        self.ucRgTX = data["BufferTx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 16:
                        self.auxSpi["Write16"] = True
                        self.usRgTX = data["BufferTx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 32:
                        if nrCnt == 1:
                            self.auxSpi["WriteOne"] = True
                            self.cBits = c_int(32)
                            self.vTX = data["BufferTx"][0]
                        else:
                            self.auxSpi["Write32"] = True
                            self.uiRgTX = data["BufferTx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                
                if bWrite and bRead:
                    # default values, might be changed (computed differently)
                    self.cDQ = c_int(1)
                    self.cBitPerWord = c_int(16)
                    self.cTX = c_int(nrCnt)
                    self.cRX = c_int(nrCnt)
                    if format == 8:
                        self.auxSpi["WriteRead"] = True
                        self.ucRgTX = data["BufferTx"]
                        self.ucRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 16:
                        self.auxSpi["WriteRead16"] = True
                        self.usRgTX = data["BufferTx"]
                        self.usRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 32:
                        self.auxSpi["WriteRead32"] = True
                        self.uiRgTX = data["BufferTx"]
                        self.uiRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                
                # cmd write/read op
                if data["Cmd"] != 0 and bRead:
                    # default values, might be changed (computed differently)
                    self.cBitCmd = c_int(8)
                    self.cmd = c_int(data["Cmd"])
                    self.cDummy = c_int(0)
                    self.cDQ = c_int(1)
                    self.cBitPerWord = c_int(16)
                    self.cRX = c_int(nrCnt)
                    if format == 8:
                        self.auxSpi["CmdRead"] = True
                        # default values, might be changed (computed differently)
                        self.ucRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 16:
                        self.auxSpi["CmdRead16"] = True
                        # default values, might be changed (computed differently)
                        self.usRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 32:
                        if nrCnt == 1:
                            self.auxSpi["CmdReadOne"] = True
                            self.pRX = data["BufferRx"]
                        else:
                            self.auxSpi["CmdRead32"] = True
                            self.uiRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                
                if data["Cmd"] != 0 and bWrite:
                    # default values, might be changed (computed differently)
                    self.cBitCmd = c_int(8)
                    self.cmd = c_int(data["Cmd"])
                    self.cDummy = c_int(0)
                    self.cDQ = c_int(1)
                    self.cBitPerWord = c_int(16)
                    self.cTX = c_int(nrCnt)
                    if format == 8:
                        self.auxSpi["CmdWrite"] = True
                        # default values, might be changed (computed differently)
                        self.ucRgTX = data["BufferTx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 16:
                        self.auxSpi["CmdWrite16"] = True
                        # default values, might be changed (computed differently)
                        self.usRgTX = data["BufferTx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 32:
                        if nrCnt == 1:
                            self.auxSpi["CmdWriteOne"] = True
                            self.vTX = data["BufferTx"]
                        else:
                            self.auxSpi["CmdWrite32"] = True
                            self.uiRgTX = data["BufferTx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                
                if ((data["Cmd"] != 0 and bWrite) and bRead):
                    # default values, might be changed (computed differently)
                    self.cBitCmd = c_int(8)
                    self.cmd = c_int(data["Cmd"])
                    self.cDummy = c_int(0)
                    self.cDQ = c_int(1)
                    self.cBitPerWord = c_int(16)
                    self.cRX = c_int(nrCnt)
                    self.cTX = c_int(nrCnt)
                    if format == 8:
                        self.auxSpi["CmdWriteRead"] = True
                        self.ucRgTX = data["BufferTx"]
                        self.ucRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 16:
                        self.auxSpi["CmdWriteRead16"] = True
                        self.usRgTX = data["BufferTx"]
                        self.usRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
                    elif format == 32:
                        self.auxSpi["CmdWriteRead32"] = True
                        self.uiRgTX = data["BufferTx"]
                        self.uiRgRX = data["BufferRx"]
                        iRet = self.cntrlDigitalSpi(dSpi=self.auxSpi, bSet=False)
            
            except ErrorWpFnGenericInstrument as err:
                print(err)

        def I2c(self,
                bReset=False,
                frequency=0.0,
                bNak=False,
                bClear=False,
                bStretch=False,
                bRead=False,
                bWrite=False,
                bSpy=False,
                nrCnt=1,
                chDIOScl=None,
                chDIOSda=None,
                timeout=0.0,
                data={"Nak":0,"Clear":0,"BufferRx":[],
                      "BufferTx":[],"Addr":0,"BufferSpy":[],
                      "SpyCntData":0,"SpyStartStop":(0,0)}
                ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            """
            try:
                # reset, freq(hz)
                self.auxI2c["Reset"] = bReset
                if frequency >= 0.0:
                    self.auxI2c["Rate"] = True
                    self.hz = c_double(frequency)
                else:
                    raise ErrorWpFnGenericInstrument("I2c error: Negative frequency")
                iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=True)
                # scl, sda idx
                if ((chDIOScl is not None and chDIOSda is not None) and
                    (chDIOScl <= 15 and chDIOSda >= 0)
                    ):
                    self.idxChannel = c_int(chDIOScl)
                    self.auxSpi["Scl"] = True
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=False)
                    self.auxSpi["Sda"] = True
                    self.idxSelect = c_int(chDIOSda)
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=True)
                else:
                    raise ErrorWpFnGenericInstrument("I2c error: Scl, Sda channels not set")
                # timeout
                if timeout >= 0.0:
                    self.auxI2c["Timeout"] = True
                    self.sec = c_double(timeout)
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=True)
                # nak
                if bNak:
                    self.auxI2c["ReadNak"] = True
                    self.fNakLastReadByte = c_int(data["Nak"])
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=True)
                # clear
                if bClear:
                    self.auxI2c["Clear"] = True
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=False)
                    data["Clear"] = self.retFFree
                # stretch ~ ck signal
                if bStretch:
                    self.auxI2c["Stretch"] = True
                    self.fEnable = c_int(1)
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=True)
                # read
                if bRead:
                    self.auxI2c["Read"] = True
                    self.adr8bits = c_ubyte(data["Addr"])
                    self.ucRgbRx = data["BufferRx"]
                    self.cRx = c_int(nrCnt)
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=False)
                    data["Nak"] = self.retNak.value
                # write
                if bWrite:
                    self.auxI2c["Write"] = True
                    self.adr8bits = c_ubyte(data["Addr"])
                    self.ucRgbTx = data["BufferTx"]
                    self.cTx = c_int(nrCnt)
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=False)
                    data["Nak"] = self.retNak.value
                # write/read op
                if bWrite and bRead:
                    self.auxI2c["WriteRead"] = True
                    self.adr8bits = c_ubyte(data["Addr"])
                    self.ucRgbTx = data["BufferTx"]
                    self.cTx = c_int(nrCnt)
                    self.ucRgRx = data["BufferRx"]
                    self.cRx = c_int(nrCnt)
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=False)
                    data["Nak"] = self.retNak.value
                # spy
                if bSpy:
                    self.auxI2c["SpyStart"] = True
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=False)
                    self.auxI2c["SpyStatus"] = True
                    self.ucRgData = data["BufferSpy"]
                    iRet = self.cntrlDigitalI2c(dI2c=self.auxI2c, bSet=False)
                    data["SpyCntData"] = self.cData
                    data["SpyStartStop"][0] = self.retFStart
                    data["SpyStartStop"][1] = self.retFStop
                    data["Nak"] = self.retINak
            
            except ErrorWpFnGenericInstrument as err:
                print(err)

        def Can(self,
                bReset=False,
                frequency=0.0,
                bRead=False,
                bWrite=False,
                chDIOTx=None,
                chDIORx=None,
                nrCntRx=1,
                data={"Polarity":0,"ID":0,"BufferTx":[],
                      "BufferRx":[],"DLC":0,"Extended":0,
                      "Remote":0,"Status":0}
                ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            """
            try:
                iRet = 0
                # reset, freq(hz)
                self.auxCan["Reset"] = bReset
                if frequency >= 0.0:
                    self.auxCan["Rate"] = True
                    self.hz = c_double(frequency)
                else:
                    raise ErrorWpFnGenericInstrument("Can error: Negative frequency")
                iRet = self.cntrlDigitalCan(dCan=self.auxCan, bSet=True)
                if ((chDIOTx is not None and chDIORx is not None) and
                    (chDIOTx <= 15 and chDIOTx >= 0) and
                    (chDIORx <= 15 and chDIORx >= 0)
                    ):
                    # Tx dio
                    self.idxChannel = c_int(chDIOTx)
                    self.auxCan["Tx"] = True
                    iRet = self.cntrlDigitalCan(dCan=self.auxCan, bSet=True)
                    # Rx dio
                    self.idxChannel = c_int(chDIORx)
                    self.auxCan["Rx"] = True
                    iRet = self.cntrlDigitalCan(dCan=self.auxCan, bSet=True)
                else:
                    raise ErrorWpFnGenericInstrument("Can error: Tx and Rx channels not set")
                # polarity
                self.polarity = c_int(data["Polarity"])
                self.auxCan["Polarity"] = True
                iRet = self.cntrlDigitalCan(dCan=self.auxCan, bSet=True)
                if bWrite:
                    # ID, Extended, Remote, DLC, Tx
                    self.ucRgTX = data["BufferTx"]
                    self.vID = c_int(data["ID"])
                    self.fExtended = c_int(0)
                    self.fRemote = c_int(0)
                    self.cDLC = c_int(data["DLC"])
                    self.auxCan["Tx"] = True
                    iRet = self.cntrlDigitalCan(dCan=self.auxCan, bSet=False)
                if bRead:
                    # ID, Extended, Remote, DLC, Rx, cRX, Status
                    self.ucRgRx = data["BufferRx"]
                    self.cRX = c_int(nrCntRx)
                    self.auxCan["Rx"] = True
                    iRet = self.cntrlDigitalCan(dCan=self.auxCan, bSet=False)
                    data["ID"] = self.retVID.value
                    data["Extended"] = self.retFExtended.value
                    data["Remote"] = self.retFRemote.value
                    data["DLC"] = self.retCDLC.value
                    data["Status"] = self.retVStatus.value
            
            except ErrorWpFnGenericInstrument as err:
                print(err)

        def Swd(self,
                bReset=False,
                frequency=0.0,
                chDIOCk=None,
                chDIOIo=None,
                # See what Turn/Trail means for Swd protocol.
                bPark=False,
                bNak=False,
                bIdle=False,
                bClear=False,
                bRead=False,
                bWrite=False,
                data={"Turn":0,"Trail":0,"Drive":0,
                      "Continue":0,"High":0,"CmdTx":0,
                      "CmdRx":0,"Ack":0,"Crc":0,
                      "Reset":0,"APnDP":0,"A32":0}
                ):
            """
            @Description
            @Parameters
            @Return
            None
            @Notes
            """
            try:
                iRet = 0
                # reset, freq(hz)
                self.auxSwd["Reset"] = bReset
                if frequency >= 0.0:
                    self.auxSwd["Rate"] = True
                    self.hz = c_double(frequency)
                else:
                    raise ErrorWpFnGenericInstrument("Swd error: Negative frequency")
                iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=True)
                if ((chDIOCk is not None and chDIOIo is not None) and
                    (chDIOCk <= 15 and chDIOCk >= 0) and
                    (chDIOIo <= 15 and chDIOIo >= 0)
                    ):
                    # Ck dio
                    self.idxChannel = c_int(chDIOCk)
                    self.auxCan["Ck"] = True
                    iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=True)
                    # Io dio
                    self.idxChannel = c_int(chDIOIo)
                    self.auxCan["Io"] = True
                    iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=True)
                else:
                    raise ErrorWpFnGenericInstrument("Swd error: Ck and Io channels not set")
                # turn
                self.auxSwd["Turn"] = True
                self.cTurn = c_int(data["Turn"])
                iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=True)
                # trail
                self.auxSwd["Trail"] = True
                self.cTurn = c_int(data["Trail"])
                iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=True)
                # drive ~ park
                if bPark:
                    self.auxSwd["Park"] = True
                    self.fDrive = c_int(data["Drive"])
                    iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=True)
                # continue ~ nak
                if bNak:
                    self.auxSwd["Nak"] = True
                    self.fDrive = c_int(data["Nak"])
                    iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=True)
                # high ~ idle
                if bIdle:
                    self.auxSwd["IoIdle"] = True
                    self.fDrive = c_int(data["High"])
                    iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=True)
                # clear
                if bClear:
                    self.auxSwd["Clear"] = True
                    self.cReset = c_int(data["Reset"])
                    self.cTurn = c_int(data["Turn"])
                    iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=False)
                # Tx ~ APnDP, A32, Ack, Write
                if bWrite:
                    self.auxSwd["Write"] = True
                    self.APnDP = c_int(data["APnDP"])
                    self.A32 = c_int(data["A32"])
                    self.Write = c_int(data["CmdTx"])
                    iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=False)
                    data["Ack"] = self.retAck.value
                # Rx ~ APnDP, A32, Ack, Read, Crc
                if bRead:
                    self.auxSwd["Read"] = True
                    self.APnDP = c_int(data["APnDP"])
                    self.A32 = c_int(data["A32"])
                    iRet = self.cntrlDigitalSwd(dSwd=self.auxSwd, bSet=False)
                    data["Ack"] = self.retAck.value
                    data["CmdRx"] = self.retRead.value
                    data["Crc"] = self.retCrc.value
            
            except ErrorWpFnGenericInstrument as err:
                print(err)

    def __init__(self,
                 iHnd : c_int
                 ):
        #self.dr = DigitalResources()
        self._io = DigitalInstruments.IOConfig(iHnd)
        #self._lac = DigitalInstruments.LogicAnalyzerConfig(iHnd)
        #self._pgc = DigitalInstruments.PatternGeneratorConfig(iHnd)
        self._dpc = DigitalInstruments.DigitalProtocolsConfig(iHnd)

    @property
    def io(self):
        """ Get reference for self._io """
        return self._io

#    @property
#    def lac(self):
#        """ Get reference for self._lac """
#        return self._lac

#    @property
#    def pgc(self):
#        """ Get reference for self._pgc """
#        return self._pgc

    @property
    def dpc(self):
        """ Get reference for self._dpc """
        return self._dpc
