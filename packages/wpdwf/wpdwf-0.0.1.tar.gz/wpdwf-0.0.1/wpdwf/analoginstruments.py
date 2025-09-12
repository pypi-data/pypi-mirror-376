
# Custom files
from wfoptionsconstants import DwfSymbolsConstants as wdsc
from enumfuncconstants import DwfFuncCorrelationAnalog
from wfoptionsconstants import (DwfSymbolsConstants, DwfFnParamOpt)
from dwfresource import BindingsLinkUp
from dwfexeptions import ErrorWpFnGenericInstrument

# Stdlib file(s)
from ctypes import (CFUNCTYPE, POINTER, c_char,
                    c_int, c_ubyte, create_string_buffer,
                    c_uint, c_double, c_ulonglong,
                    c_void_p, c_ushort)

class Oscilloscope:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationAnalog.cFDwfAnalogInReset, # Control and status
            DwfFuncCorrelationAnalog.cFDwfAnalogInConfigure,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerForce,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusSamplesLeft,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusSamplesValid,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusIndexWrite,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusAutoTriggered,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusData,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusData2,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusData16,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusDataMix16,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusNoise,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusNoise2,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusSample,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusTime,
            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusRecord,
            DwfFuncCorrelationAnalog.cFDwfAnalogInRecordLengthSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInRecordLengthGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInCounterInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInCounterSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInCounterGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInCounterStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogInFrequencyInfo, # Acquisition configuration
            DwfFuncCorrelationAnalog.cFDwfAnalogInFrequencySet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInFrequencyGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInBitsInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInBufferSizeInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInBufferSizeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInBufferSizeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInBuffersInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInBuffersSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInBuffersGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInBuffersStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogInNoiseSizeInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInNoiseSizeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInNoiseSizeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInAcquisitionModeInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInAcquisitionModeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInAcquisitionModeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCount, # Channel configuration
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCounts,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelEnableSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelEnableGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFilterInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFilterSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFilterGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelRangeInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelRangeSteps,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelRangeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelRangeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelOffsetInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelOffsetSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelOffsetGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelAttenuationSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelAttenuationGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelBandwidthSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelBandwidthGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelImpedanceSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelImpedanceGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCouplingInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCouplingSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCouplingGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFiirInfo, # IIR filters
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFiirSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelWindowSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCustomWindowSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerSourceSet, # Trigger configuration
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerSourceGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerPositionInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerPositionSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerPositionGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerPositionStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerAutoTimeoutInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerAutoTimeoutSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerAutoTimeoutGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHoldOffInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHoldOffSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHoldOffGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerTypeInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerTypeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerTypeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerChannelInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerChannelSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerChannelGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerFilterInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerFilterSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerFilterGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLevelInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLevelSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLevelGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHysteresisInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHysteresisSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHysteresisGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerConditionInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerConditionSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerConditionGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthConditionInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthConditionSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthConditionGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingSourceSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingSourceGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingSlopeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingSlopeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingDelaySet,
            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingDelayGet
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfAnalogInReset, # Control and status
            BindingsLinkUp.resDwf.FDwfAnalogInConfigure,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerForce,
            BindingsLinkUp.resDwf.FDwfAnalogInStatus,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusSamplesLeft,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusSamplesValid,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusIndexWrite,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusAutoTriggered,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusData,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusData2,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusData16,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusDataMix16,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusNoise,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusNoise2,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusSample,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusTime,
            BindingsLinkUp.resDwf.FDwfAnalogInStatusRecord,
            BindingsLinkUp.resDwf.FDwfAnalogInRecordLengthSet,
            BindingsLinkUp.resDwf.FDwfAnalogInRecordLengthGet,
            BindingsLinkUp.resDwf.FDwfAnalogInCounterInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInCounterSet,
            BindingsLinkUp.resDwf.FDwfAnalogInCounterGet,
            BindingsLinkUp.resDwf.FDwfAnalogInCounterStatus,
            BindingsLinkUp.resDwf.FDwfAnalogInFrequencyInfo, # Acquisition configuration
            BindingsLinkUp.resDwf.FDwfAnalogInFrequencySet,
            BindingsLinkUp.resDwf.FDwfAnalogInFrequencyGet,
            BindingsLinkUp.resDwf.FDwfAnalogInBitsInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInBufferSizeInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInBufferSizeSet,
            BindingsLinkUp.resDwf.FDwfAnalogInBufferSizeGet,
            BindingsLinkUp.resDwf.FDwfAnalogInBuffersInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInBuffersSet,
            BindingsLinkUp.resDwf.FDwfAnalogInBuffersGet,
            BindingsLinkUp.resDwf.FDwfAnalogInBuffersStatus,
            BindingsLinkUp.resDwf.FDwfAnalogInNoiseSizeInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInNoiseSizeSet,
            BindingsLinkUp.resDwf.FDwfAnalogInNoiseSizeGet,
            BindingsLinkUp.resDwf.FDwfAnalogInAcquisitionModeInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInAcquisitionModeSet,
            BindingsLinkUp.resDwf.FDwfAnalogInAcquisitionModeGet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelCount, # Channel configuration
            BindingsLinkUp.resDwf.FDwfAnalogInChannelCounts,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelEnableSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelEnableGet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelFilterInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelFilterSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelFilterGet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelRangeInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelRangeSteps,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelRangeSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelRangeGet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelOffsetInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelOffsetSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelOffsetGet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelAttenuationSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelAttenuationGet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelBandwidthSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelBandwidthGet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelImpedanceSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelImpedanceGet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelCouplingInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelCouplingSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelCouplingGet, # IIR filters
            BindingsLinkUp.resDwf.FDwfAnalogInChannelFiirInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelFiirSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelWindowSet,
            BindingsLinkUp.resDwf.FDwfAnalogInChannelCustomWindowSet, # Trigger configuration
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerSourceSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerSourceGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerPositionInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerPositionSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerPositionGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerPositionStatus,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerAutoTimeoutInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerAutoTimeoutSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerAutoTimeoutGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerHoldOffInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerHoldOffSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerHoldOffGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerTypeInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerTypeSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerTypeGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerChannelInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerChannelSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerChannelGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerFilterInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerFilterSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerFilterGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLevelInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLevelSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLevelGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerHysteresisInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerHysteresisSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerHysteresisGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerConditionInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerConditionSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerConditionGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLengthInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLengthSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLengthGet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLengthConditionInfo,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLengthConditionSet,
            BindingsLinkUp.resDwf.FDwfAnalogInTriggerLengthConditionGet,
            BindingsLinkUp.resDwf.FDwfAnalogInSamplingSourceSet,
            BindingsLinkUp.resDwf.FDwfAnalogInSamplingSourceGet,
            BindingsLinkUp.resDwf.FDwfAnalogInSamplingSlopeSet,
            BindingsLinkUp.resDwf.FDwfAnalogInSamplingSlopeGet,
            BindingsLinkUp.resDwf.FDwfAnalogInSamplingDelaySet,
            BindingsLinkUp.resDwf.FDwfAnalogInSamplingDelayGet
        ]
        self._dtFuncOsc = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncOsc) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncOsc[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncOsc(self) -> dict:
        """ Get reference for self._dtFuncOsc """
        return self._dtFuncOsc

class ArbitraryWaveformGenerator:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationAnalog.cFDwfAnalogOutCount, # Configuration
            DwfFuncCorrelationAnalog.cFDwfAnalogOutMasterSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutMasterGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutTriggerSourceSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutTriggerSourceGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutTriggerSlopeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutTriggerSlopeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRunInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRunSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRunGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRunStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutWaitInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutWaitSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutWaitGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRepeatInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRepeatSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRepeatGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRepeatStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRepeatTriggerSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutRepeatTriggerGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutLimitationInfo, # EExplorer, DPS3340 channel 3&4 current/voltage limitation
            DwfFuncCorrelationAnalog.cFDwfAnalogOutLimitationSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutLimitationGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutModeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutModeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutIdleInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutIdleSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutIdleGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeEnableSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeEnableGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeFunctionInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeFunctionSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeFunctionGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeFrequencyInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeFrequencySet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeFrequencyGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeAmplitudeInfo, # Carrier Amplitude or Modulation Index
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeAmplitudeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeAmplitudeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeOffsetInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeOffsetSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeOffsetGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeSymmetryInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeSymmetrySet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeSymmetryGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodePhaseInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodePhaseSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodePhaseGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeDataInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodeDataSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutCustomAMFMEnableSet, # Needed for EExplorer, not used for Analog Discovery
            DwfFuncCorrelationAnalog.cFDwfAnalogOutCustomAMFMEnableGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutReset, # Control
            DwfFuncCorrelationAnalog.cFDwfAnalogOutConfigure,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodePlayInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodePlayStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogOutNodePlayData
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfAnalogOutCount, # Configuration
            BindingsLinkUp.resDwf.FDwfAnalogOutMasterSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutMasterGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutTriggerSourceSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutTriggerSourceGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutTriggerSlopeSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutTriggerSlopeGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutRunInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutRunSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutRunGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutRunStatus,
            BindingsLinkUp.resDwf.FDwfAnalogOutWaitInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutWaitSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutWaitGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutRepeatInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutRepeatSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutRepeatGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutRepeatStatus,
            BindingsLinkUp.resDwf.FDwfAnalogOutRepeatTriggerSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutRepeatTriggerGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutLimitationInfo, # EExplorer, DPS3340 channel 3&4 current/voltage limitation
            BindingsLinkUp.resDwf.FDwfAnalogOutLimitationSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutLimitationGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutModeSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutModeGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutIdleInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutIdleSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutIdleGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeEnableSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeEnableGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeFunctionInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeFunctionSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeFunctionGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeFrequencyInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeFrequencySet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeFrequencyGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeAmplitudeInfo, # Carrier Amplitude or Modulation Index
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeAmplitudeSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeAmplitudeGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeOffsetInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeOffsetSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeOffsetGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeSymmetryInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeSymmetrySet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeSymmetryGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodePhaseInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodePhaseSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodePhaseGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeDataInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodeDataSet,
            BindingsLinkUp.resDwf.FDwfAnalogOutCustomAMFMEnableSet, # Needed for EExplorer, not used for Analog Discovery
            BindingsLinkUp.resDwf.FDwfAnalogOutCustomAMFMEnableGet,
            BindingsLinkUp.resDwf.FDwfAnalogOutReset, # Control
            BindingsLinkUp.resDwf.FDwfAnalogOutConfigure,
            BindingsLinkUp.resDwf.FDwfAnalogOutStatus,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodePlayInfo,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodePlayStatus,
            BindingsLinkUp.resDwf.FDwfAnalogOutNodePlayData
        ]
        self._dtFuncAWG = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncAWG) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncAWG[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncAWG(self) -> dict:
        """ Get reference for self._dtFuncAWG """
        return self._dtFuncAWG

class AnalogIO:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationAnalog.cFDwfAnalogIOReset, # Control
            DwfFuncCorrelationAnalog.cFDwfAnalogIOConfigure,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOEnableInfo, # Configure
            DwfFuncCorrelationAnalog.cFDwfAnalogIOEnableSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOEnableGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOEnableStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelCount,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelName,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelNodeName,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelNodeInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelNodeSetInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelNodeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelNodeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelNodeStatusInfo,
            DwfFuncCorrelationAnalog.cFDwfAnalogIOChannelNodeStatus
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfAnalogIOReset, # Control
            BindingsLinkUp.resDwf.FDwfAnalogIOConfigure,
            BindingsLinkUp.resDwf.FDwfAnalogIOStatus,
            BindingsLinkUp.resDwf.FDwfAnalogIOEnableInfo, # Configure
            BindingsLinkUp.resDwf.FDwfAnalogIOEnableSet,
            BindingsLinkUp.resDwf.FDwfAnalogIOEnableGet,
            BindingsLinkUp.resDwf.FDwfAnalogIOEnableStatus,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelCount,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelName,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelInfo,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelNodeName,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelNodeInfo,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelNodeSetInfo,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelNodeSet,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelNodeGet,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelNodeStatusInfo,
            BindingsLinkUp.resDwf.FDwfAnalogIOChannelNodeStatus
        ]
        self._dtFuncAIO = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncAIO) == 0
            ):
            dSize = dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncAIO[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncAIO(self) -> dict:
        """ Get reference for self._dtFuncAIO """
        return self._dtFuncAIO

class AnalogImpedance:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceReset,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceModeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceModeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceReferenceSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceReferenceGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceFrequencySet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceFrequencyGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceAmplitudeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceAmplitudeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceOffsetSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceOffsetGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceProbeSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceProbeGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedancePeriodSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedancePeriodGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceCompReset,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceCompSet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceCompGet,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceConfigure,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceStatus,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceStatusInput,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceStatusWarning,
            DwfFuncCorrelationAnalog.cFDwfAnalogImpedanceStatusMeasure
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceReset,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceModeSet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceModeGet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceReferenceSet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceReferenceGet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceFrequencySet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceFrequencyGet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceAmplitudeSet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceAmplitudeGet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceOffsetSet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceOffsetGet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceProbeSet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceProbeGet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedancePeriodSet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedancePeriodGet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceCompReset,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceCompSet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceCompGet,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceConfigure,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceStatus,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceStatusInput,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceStatusWarning,
            BindingsLinkUp.resDwf.FDwfAnalogImpedanceStatusMeasure
        ]
        self._dtFuncAI = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncAI) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncAI[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncAI(self) -> dict:
        """ Get reference for self._dtFuncAI """
        return self._dtFuncAI

class AnalogResources:
    """
    @Description
    @Notes
    """
    def __init__(self):
        #self.osc = Oscilloscope()
        #self.awg = ArbitraryWaveformGenerator()
        #self.aio = AnalogIO()
        #self.aimpd = AnalogImpedance()
        pass

class AnalogInstruments:
    """
    @Description
    This class implements access to all instruments
    similar to signal generator, spectrum analyzer.
    @Notes
    None
    """
    def __init__(self, iHnd=None):
        #self.cs = ControlStatus()
        #self.ac = AcquisitionConfig()
        #self.cc = ChannelConfig()
        #self.flt = Filters()
        #self.tc = TriggerConfig()
        pass

    class ControlStatus:
        """
        @Description
        @Notes
        """
        def __init__(self, iHnd=None):
            self.osc = Oscilloscope()
            self.dtFuncOsc = self.osc.dtFuncOsc

        def WpDwfAnalogInReset(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInReset
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfAnalogInConfigure(self,
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
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int)
            def WpFnGeneric(hdwf, fReconfigure, fStart) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInConfigure
                          )(hdwf, fReconfigure, fStart)
                return iretVal
            return WpFnGeneric(hdwf, fReconfigure, fStart)

        def WpDwfAnalogInTriggerForce(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerForce
                          )(hdwf)
                return iretVal
            return WpFnGeneric(hdwf)

        def WpDwfAnalogInStatus(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatus
                          )(hdwf, fReadData, psts)
                return iretVal
            return WpFnGeneric(hdwf, fReadData, psts)

        def WpDwfAnalogInStatusSamplesLeft(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusSamplesLeft
                          )(hdwf, pcSamplesLeft)
                return iretVal
            return WpFnGeneric(hdwf, pcSamplesLeft)

        def WpDwfAnalogInStatusSamplesValid(self,
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
            @CFUNCTYPE(c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pcSamplesLeft) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusSamplesValid
                          )(hdwf, pcSamplesLeft)
                return iretVal
            return WpFnGeneric(hdwf, pcSamplesLeft)

        def WpDwfAnalogInStatusIndexWrite(self,
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
            @CFUNCTYPE(c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pidxWrite) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusIndexWrite
                          )(hdwf, pidxWrite)
                return iretVal
            return WpFnGeneric(hdwf, pidxWrite)

        def WpDwfAnalogInStatusAutoTriggered(self,
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
            @CFUNCTYPE(c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfAuto) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusAutoTriggered
                          )(hdwf, pfAuto)
                return iretVal
            return WpFnGeneric(hdwf, pfAuto)

        def WpDwfAnalogInStatusData(self,
                                    hdwf : c_int,
                                    idxChannel : c_int,
                                    rgdVoltData : POINTER(c_double),
                                    cdData : c_int
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
                       POINTER(c_double), c_int)
            def WpFnGeneric(hdwf, idxChannel, rgdVoltData,
                            cdData) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusData
                          )(hdwf, idxChannel, rgdVoltData,
                            cdData)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, rgdVoltData,
                               cdData)

        def WpDwfAnalogInStatusData2(self,
                                     hdwf : c_int,
                                     idxChannel : c_int,
                                     rgdVoltData : POINTER(c_double),
                                     idxData : c_int,
                                     cdData : c_int
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
                       POINTER(c_double), c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel, rgdVoltData,
                            idxData, cdData) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusData2
                          )(hdwf, idxChannel, rgdVoltData,
                            idxData, cdData)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, rgdVoltData,
                               idxData, cdData)

        def WpDwfAnalogInStatusData16(self,
                                      hdwf : c_int,
                                      idxChannel : c_int,
                                      rgu16Data : POINTER(c_ushort),
                                      idxData : c_int,
                                      cdData : c_int
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
                       POINTER(c_ushort), c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel, rgu16Data,
                            idxData, cdData) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusData16
                          )(hdwf, idxChannel, rgu16Data,
                            idxData, cdData)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, rgu16Data,
                               idxData, cdData)

        def WpDwfAnalogInStatusDataMix16(self,
                                         hdwf : c_int,
                                         rgu16Data : POINTER(c_ushort),
                                         idxData : c_int,
                                         cdData : c_int
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_ushort),
                       c_int, c_int)
            def WpFnGeneric(hdwf, rgu16Data, idxData,
                            cdData) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusDataMix16
                          )(hdwf, rgu16Data, idxData,
                            cdData)
                return iretVal
            return WpFnGeneric(hdwf, rgu16Data, idxData,
                               cdData)

        def WpDwfAnalogInStatusNoise(self,
                                     hdwf : c_int,
                                     idxChannel : c_int,
                                     rgdMin : POINTER(c_double),
                                     rgdMax : POINTER(c_double),
                                     cdData : c_int
                                     ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, c_int, POINTER(c_double),
                       POINTER(c_double), c_int)
            def WpFnGeneric(hdwf, idxChannel, rgdMin,
                            rgdMax, cdData) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusNoise
                          )(hdwf, idxChannel, rgdMin,
                            rgdMax, cdData)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, rgdMin,
                               rgdMax, cdData)

        def WpDwfAnalogInStatusNoise2(self,
                                      hdwf : c_int,
                                      idxChannel : c_int,
                                      rgdMin : POINTER(c_double),
                                      rgdMax : POINTER(c_double),
                                      idxData : c_int,
                                      cdData : c_int
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
                       POINTER(c_double), POINTER(c_double), c_int,
                       c_int)
            def WpFnGeneric(hdwf, idxChannel, rgdMin,
                            rgdMax, idxData, cdData) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusNoise2
                          )(hdwf, idxChannel, rgdMin,
                            rgdMax, idxData, cdData)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, rgdMin,
                               rgdMax, idxData, cdData)

        def WpDwfAnalogInStatusSample(self,
                                      hdwf : c_int,
                                      idxChannel : c_int,
                                      pdVoltSample : POINTER(c_double)
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
                       POINTER(c_double))
            def WpFnGeneric(hdwf, idxChannel, pdVoltSample) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusSample
                          )(hdwf, idxChannel, pdVoltSample)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pdVoltSample)

        def WpDwfAnalogInStatusTime(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusTime
                          )(hdwf, psecUtc, ptick,
                            pticksPerSecond)
                return iretVal
            return WpFnGeneric(hdwf, psecUtc, ptick,
                               pticksPerSecond)

        def WpDwfAnalogInStatusRecord(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInStatusRecord
                          )(hdwf, pcdDataAvailable, pcdDataLost,
                            pcdDataCorrupt)
                return iretVal
            return WpFnGeneric(hdwf, pcdDataAvailable, pcdDataLost,
                               pcdDataCorrupt)

        def WpDwfAnalogInRecordLengthSet(self,
                                         hdwf : c_int,
                                         sLength : c_double
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
            def WpFnGeneric(hdwf, sLength) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInRecordLengthSet
                          )(hdwf, sLength)
                return iretVal
            return WpFnGeneric(hdwf, sLength)

        def WpDwfAnalogInRecordLengthGet(self,
                                         hdwf : c_int,
                                         psLength : POINTER(c_double)
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
            def WpFnGeneric(hdwf, psLength) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInRecordLengthGet
                          )(hdwf, psLength)
                return iretVal
            return WpFnGeneric(hdwf, psLength)

        def WpDwfAnalogInCounterInfo(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInCounterInfo
                          )(hdwf, pcntMax, psecMax)
                return iretVal
            return WpFnGeneric(hdwf, pcntMax, psecMax)

        def WpDwfAnalogInCounterSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInCounterSet
                          )(hdwf, sec)
                return iretVal
            return WpFnGeneric(hdwf, sec)

        def WpDwfAnalogInCounterGet(self,
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
            @CFUNCTYPE(c_int, c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, psec) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInCounterGet
                          )(hdwf, psec)
                return iretVal
            return WpFnGeneric(hdwf, psec)

        def WpDwfAnalogInCounterStatus(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInCounterStatus
                          )(hdwf, pcnt, pfreq,
                            ptick)
                return iretVal
            return WpFnGeneric(hdwf, pcnt, pfreq,
                               ptick)

    class AcquisitionConfig:
        """
        @Description
        @Notes
        """
        def __init__(self, iHnd=None):
            self.osc = Oscilloscope()
            self.dtFuncOsc = self.osc.dtFuncOsc

        def WpDwfAnalogInFrequencyInfo(self,
                                       hdwf : c_int,
                                       phzMin : POINTER(c_double),
                                       phzMax : POINTER(c_double)
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
            def WpFnGeneric(hdwf, phzMin, phzMax) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInFrequencyInfo
                          )(hdwf, phzMin, phzMax)
                return iretVal
            return WpFnGeneric(hdwf, phzMin, phzMax)

        def WpDwfAnalogInFrequencySet(self,
                                      hdwf : c_int,
                                      hzFrequency : c_double
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
            def WpFnGeneric(hdwf, hzFrequency) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInFrequencySet
                          )(hdwf, hzFrequency)
                return iretVal
            return WpFnGeneric(hdwf, hzFrequency)

        def WpDwfAnalogInFrequencyGet(self,
                                      hdwf : c_int,
                                      phzFrequency : POINTER(c_double)
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
            def WpFnGeneric(hdwf, phzFrequency) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInFrequencyGet
                          )(hdwf, phzFrequency)
                return iretVal
            return WpFnGeneric(hdwf, phzFrequency)

        def WpDwfAnalogInBitsInfo(self,
                                  hdwf : c_int,
                                  pnBits : POINTER(c_int)
                                  ) -> int:
            """
            @Description
            Returns the number of ADC bits.
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pnBits) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInBitsInfo
                          )(hdwf, pnBits)
                return iretVal
            return WpFnGeneric(hdwf, pnBits)

        def WpDwfAnalogInBufferSizeInfo(self,
                                        hdwf : c_int,
                                        pnSizeMin : POINTER(c_int),
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
            @CFUNCTYPE(c_int, hdwf, POINTER(c_int),
                       POINTER(c_int))
            def WpFnGeneric(hdwf, pnSizeMin, pnSizeMax) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInBufferSizeInfo
                          )(hdwf, pnSizeMin, pnSizeMax)
                return iretVal
            return WpFnGeneric(hdwf, pnSizeMin, pnSizeMax)

        def WpDwfAnalogInBufferSizeSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInBufferSizeSet
                          )(hdwf, nSize)
                return iretVal
            return WpFnGeneric(hdwf, nSize)

        def WpDwfAnalogInBufferSizeGet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInBufferSizeGet
                          )(hdwf, pnSize)
                return iretVal
            return WpFnGeneric(hdwf, pnSize)

        def WpDwfAnalogInBuffersInfo(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInBuffersInfo
                          )(hdwf, pMax)
                return iretVal
            return WpFnGeneric(hdwf, pMax)

        def WpDwfAnalogInBuffersSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInBuffersSet
                          )(hdwf, n)
                return iretVal
            return WpFnGeneric(hdwf, n)

        def WpDwfAnalogInBuffersGet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInBuffersGet
                          )(hdwf, pn)
                return iretVal
            return WpFnGeneric(hdwf, pn)

        def WpDwfAnalogInBuffersStatus(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInBuffersStatus
                          )(hdwf, pn)
                return iretVal
            return WpFnGeneric(hdwf, )

        def WpDwfAnalogInNoiseSizeInfo(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInNoiseSizeInfo
                          )(hdwf, pnSizeMax)
                return iretVal
            return WpFnGeneric(hdwf, pnSizeMax)

        def WpDwfAnalogInNoiseSizeSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInNoiseSizeSet
                          )(hdwf, nSize)
                return iretVal
            return WpFnGeneric(hdwf, nSize)

        def WpDwfAnalogInNoiseSizeGet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInNoiseSizeGet
                          )(hdwf, pnSize)
                return iretVal
            return WpFnGeneric(hdwf, pnSize)

        def WpDwfAnalogInAcquisitionModeInfo(self,
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
            use IsBitSet
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfsacqmode) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInAcquisitionModeInfo
                          )(hdwf, pfsacqmode)
                return iretVal
            return WpFnGeneric(hdwf, pfsacqmode)

        def WpDwfAnalogInAcquisitionModeSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInAcquisitionModeSet
                          )(hdwf, acqmode)
                return iretVal
            return WpFnGeneric(hdwf, acqmode)

        def WpDwfAnalogInAcquisitionModeGet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInAcquisitionModeGet
                          )(hdwf, pacqmode)
                return iretVal
            return WpFnGeneric(hdwf, pacqmode)

    class ChannelConfig:
        """
        @Description
        @Notes
        """
        def __init__(self, iHnd=None):
            self.osc = Oscilloscope()
            self.dtFuncOsc = self.osc.dtFuncOsc

        def WpDwfAnalogInChannelCount(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCount
                          )(hdwf, pcChannel)
                return iretVal
            return WpFnGeneric(hdwf, pcChannel)

        def WpDwfAnalogInChannelCounts(self,
                                       hdwf : c_int,
                                       pcReal : POINTER(c_int),
                                       pcFilter : POINTER(c_int),
                                       pcTotal : POINTER(c_int)
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
            def WpFnGeneric(hdwf, pcReal, pcFilter,
                            pcTotal) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCounts
                          )(hdwf, pcReal, pcFilter,
                            pcTotal)
                return iretVal
            return WpFnGeneric(hdwf, pcReal, pcFilter,
                               pcTotal)

        def WpDwfAnalogInChannelEnableSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelEnableSet
                          )(hdwf, idxChannel, fEnable)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, fEnable)

        def WpDwfAnalogInChannelEnableGet(self,
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
            @CFUNCTYPE(c_int, c_int, c_int,
                       POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, pfEnable) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelEnableGet
                          )(hdwf, idxChannel, pfEnable)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pfEnable)

        def WpDwfAnalogInChannelFilterInfo(self,
                                           hdwf : c_int,
                                           pfsfilter : POINTER(c_int)
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            use IsBitSet
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfsfilter) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFilterInfo
                          )(hdwf, pfsfilter)
                return iretVal
            return WpFnGeneric(hdwf, pfsfilter)

        def WpDwfAnalogInChannelFilterSet(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          filter : c_int
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
            def WpFnGeneric(hdwf, idxChannel, filter) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFilterSet
                          )(hdwf, idxChannel, filter)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, filter)

        def WpDwfAnalogInChannelFilterGet(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          pfilter : POINTER(c_int)
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
            def WpFnGeneric(hdwf, idxChannel, pfilter) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFilterGet
                          )(hdwf, idxChannel, pfilter)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pfilter)

        def WpDwfAnalogInChannelRangeInfo(self,
                                          hdwf : c_int,
                                          pvoltsMin : POINTER(c_double),
                                          pvoltsMax : POINTER(c_double),
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
            def WpFnGeneric(hdwf, pvoltsMin, pvoltsMax,
                            pnSteps) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelRangeInfo
                          )(hdwf, pvoltsMin, pvoltsMax,
                            pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, pvoltsMin, pvoltsMax,
                               pnSteps)

        def WpDwfAnalogInChannelRangeSteps(self,
                                           hdwf : c_int,
                                           rgVoltsStep : POINTER(c_double),
                                           pnSteps : POINTER(c_int)
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            size - [32] ~ double rgVoltsStep[32]
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_double),
                       POINTER(c_int))
            def WpFnGeneric(hdwf, rgVoltsStep, pnSteps) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelRangeSteps
                          )(hdwf, rgVoltsStep, pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, rgVoltsStep, pnSteps)

        def WpDwfAnalogInChannelRangeSet(self,
                                         hdwf : c_int,
                                         idxChannel : c_int,
                                         voltsRange : c_double
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
                       c_double)
            def WpFnGeneric(hdwf, idxChannel, voltsRange) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelRangeSet
                          )(hdwf, idxChannel, voltsRange)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, voltsRange)

        def WpDwfAnalogInChannelRangeGet(self,
                                         hdwf : c_int,
                                         idxChannel : c_int,
                                         pvoltsRange : POINTER(c_double)
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
                       POINTER(c_double))
            def WpFnGeneric(hdwf, idxChannel, pvoltsRange) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelRangeGet
                          )(hdwf, idxChannel, pvoltsRange)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pvoltsRange)

        def WpDwfAnalogInChannelOffsetInfo(self,
                                           hdwf : c_int,
                                           pvoltsMin : POINTER(c_double),
                                           pvoltsMax : POINTER(c_double),
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
            def WpFnGeneric(hdwf, pvoltsMin, pvoltsMax, pnSteps) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelOffsetInfo
                          )(hdwf, pvoltsMin, pvoltsMax, pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, pvoltsMin, pvoltsMax, pnSteps)

        def WpDwfAnalogInChannelOffsetSet(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          voltOffset : c_double
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
                       c_double)
            def WpFnGeneric(hdwf, idxChannel, voltOffset) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelOffsetSet
                          )(hdwf, idxChannel, voltOffset)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, voltOffset)

        def WpDwfAnalogInChannelOffsetGet(self,
                                         hdwf : c_int,
                                         idxChannel : c_int,
                                         pvoltOffset : POINTER(c_double)
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
                       POINTER(c_double))
            def WpFnGeneric(hdwf, idxChannel, pvoltOffset) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelOffsetGet
                          )(hdwf, idxChannel, pvoltOffset)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pvoltOffset)

        def WpDwfAnalogInChannelAttenuationSet(self,
                                              hdwf : c_int,
                                              idxChannel : c_int,
                                              xAttenuation : c_double
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
                       c_double)
            def WpFnGeneric(hdwf, idxChannel, xAttenuation) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelAttenuationSet
                          )(hdwf, idxChannel, xAttenuation)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, xAttenuation)

        def WpDwfAnalogInChannelAttenuationGet(self,
                                              hdwf : c_int,
                                              idxChannel : c_int,
                                              pxAttenuation : POINTER(c_double)
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
                       POINTER(c_double))
            def WpFnGeneric(hdwf, idxChannel, pxAttenuation) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelAttenuationGet
                          )(hdwf, idxChannel, pxAttenuation)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pxAttenuation)

        def WpDwfAnalogInChannelBandwidthSet(self,
                                            hdwf : c_int,
                                            idxChannel : c_int,
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
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_double)
            def WpFnGeneric(hdwf, idxChannel, hz) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelBandwidthSet
                          )(hdwf, idxChannel, hz)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, hz)

        def WpDwfAnalogInChannelBandwidthGet(self,
                                             hdwf : c_int,
                                             idxChannel : c_int,
                                             phz : POINTER(c_double)
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
                       POINTER(c_double))
            def WpFnGeneric(hdwf, idxChannel, phz) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelBandwidthGet
                          )(hdwf, idxChannel, phz)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, phz)

        def WpDwfAnalogInChannelImpedanceSet(self,
                                             hdwf : c_int,
                                             idxChannel : c_int,
                                             ohms : c_double
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
                       c_double)
            def WpFnGeneric(hdwf, idxChannel, ohms) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelImpedanceSet
                          )(hdwf, idxChannel, ohms)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, ohms)

        def WpDwfAnalogInChannelImpedanceGet(self,
                                             hdwf : c_int,
                                             idxChannel : c_int,
                                             pOhms : POINTER(c_double)
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
                       POINTER(c_double))
            def WpFnGeneric(hdwf, idxChannel, pOhms) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelImpedanceGet
                          )(hdwf, idxChannel, pOhms)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pOhms)

        def WpDwfAnalogInChannelCouplingInfo(self,
                                             hdwf : c_int,
                                             pfscoupling : POINTER(c_int)
                                             ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            use IsBitSet
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfscoupling) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCouplingInfo
                          )(hdwf, pfscoupling)
                return iretVal
            return WpFnGeneric(hdwf, pfscoupling)

        def WpDwfAnalogInChannelCouplingSet(self,
                                            hdwf : c_int,
                                            idxChannel : c_int,
                                            coupling : c_int
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
            def WpFnGeneric(hdwf, idxChannel, coupling) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCouplingSet
                          )(hdwf, idxChannel, coupling)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, coupling)

        def WpDwfAnalogInChannelCouplingGet(self,
                                            hdwf : c_int,
                                            idxChannel : c_int,
                                            pcoupling : POINTER(c_int)
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
            def WpFnGeneric(hdwf, idxChannel, pcoupling) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCouplingGet
                          )(hdwf, idxChannel, pcoupling)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, pcoupling)

    class Filters:
        """
        @Description
        @Notes
        FIR & IIR filters
        """
        def __init__(self, iHnd=None):
            self.osc = Oscilloscope()
            self.dtFuncOsc = self.osc.dtFuncOsc

        def WpDwfAnalogInChannelFiirInfo(self,
                                         hdwf : c_int,
                                         idxChannel : c_int,
                                         cFIR : POINTER(c_int),
                                         cIIR : POINTER(c_int)
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
                       POINTER(c_int))
            def WpFnGeneric(hdwf, idxChannel, cFIR,
                            cIIR) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFiirInfo
                          )(hdwf, idxChannel, cFIR,
                            cIIR)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, cFIR,
                               cIIR)

        def WpDwfAnalogInChannelFiirSet(self,
                                        hdwf : c_int,
                                        idxChannel : c_int,
                                        input : c_int,
                                        fiir : c_int,
                                        _pass : c_int,
                                        _ord : c_int,
                                        hz1 : c_double,
                                        hz2 : c_double,
                                        ep : c_double
                                        ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            pass -> _pass; pass ~ py keyword
            ord -> _ord; ord() ~ py built-in function
            """
            @CFUNCTYPE(c_int, c_int, c_int,
                       c_int, c_int, c_int,
                       c_int, c_double, c_double,
                       c_double)
            def WpFnGeneric(hdwf, idxChannel, input,
                            fiir, _pass, _ord,
                            hz1, hz2, ep
                            ) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelFiirSet
                          )(hdwf, idxChannel, input,
                            fiir, _pass, _ord,
                            hz1, hz2, ep)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, input,
                               fiir, _pass, _ord,
                               hz1, hz2, ep)

        def WpDwfAnalogInChannelWindowSet(self,
                                          hdwf : c_int,
                                          idxChannel : c_int,
                                          win : c_int,
                                          size : c_int,
                                          beta : c_double
                                          ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, c_int, DwfWindow,
                       c_int, c_double)
            def WpFnGeneric(hdwf, idxChannel, win,
                            size, beta) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelWindowSet
                          )(hdwf, idxChannel, win,
                            size, beta)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, win,
                               size, beta)

        def WpDwfAnalogInChannelCustomWindowSet(self,
                                                hdwf : c_int,
                                                idxChannel : c_int,
                                                rg : POINTER(c_double), # const
                                                size : c_int,
                                                normalize : c_int
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
                       POINTER(c_double), c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel, rg,
                            size, normalize) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInChannelCustomWindowSet
                          )(hdwf, idxChannel, rg,
                            size, normalize)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel, rg,
                               size, normalize)

    class TriggerConfig:
        """
        @Description
        @Notes
        """
        def __init__(self, iHnd=None):
            self.osc = Oscilloscope()
            self.dtFuncOsc = self.osc.dtFuncOsc

        def WpDwfAnalogInTriggerSourceSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerSourceSet
                          )(hdwf, trigsrc)
                return iretVal
            return WpFnGeneric(hdwf, trigsrc)

        def WpDwfAnalogInTriggerSourceGet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerSourceGet
                          )(hdwf, ptrigsrc)
                return iretVal
            return WpFnGeneric(hdwf, ptrigsrc)

        def WpDwfAnalogInTriggerPositionInfo(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerPositionInfo
                          )(hdwf, psecMin, psecMax,
                            pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, psecMin, psecMax,
                               pnSteps)

        def WpDwfAnalogInTriggerPositionSet(self,
                                            hdwf : c_int,
                                            secPosition : c_double
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
            def WpFnGeneric(hdwf, secPosition) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerPositionSet
                          )(hdwf, secPosition)
                return iretVal
            return WpFnGeneric(hdwf, secPosition)

        def WpDwfAnalogInTriggerPositionGet(self,
                                            hdwf : c_int,
                                            psecPosition : POINTER(c_double)
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
            def WpFnGeneric(hdwf, psecPosition) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerPositionGet
                          )(hdwf, psecPosition)
                return iretVal
            return WpFnGeneric(hdwf, psecPosition)

        def WpDwfAnalogInTriggerPositionStatus(self,
                                               hdwf : c_int,
                                               psecPosition : POINTER(c_double)
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
            def WpFnGeneric(hdwf, psecPosition) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerPositionStatus
                          )(hdwf, psecPosition)
                return iretVal
            return WpFnGeneric(hdwf, psecPosition)

        def WpDwfAnalogInTriggerAutoTimeoutInfo(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerAutoTimeoutInfo
                          )(hdwf, psecMin, psecMax,
                            pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, psecMin, psecMax,
                               pnSteps)

        def WpDwfAnalogInTriggerAutoTimeoutSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerAutoTimeoutSet
                          )(hdwf, secTimeout)
                return iretVal
            return WpFnGeneric(hdwf, secTimeout)

        def WpDwfAnalogInTriggerAutoTimeoutGet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerAutoTimeoutGet
                          )(hdwf, psecTimeout)
                return iretVal
            return WpFnGeneric(hdwf, psecTimeout)

        def WpDwfAnalogInTriggerHoldOffInfo(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHoldOffInfo
                          )(hdwf, psecMin, psecMax,
                            pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, psecMin, psecMax,
                               pnSteps)

        def WpDwfAnalogInTriggerHoldOffSet(self,
                                           hdwf : c_int,
                                           secHoldOff : c_double
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
            def WpFnGeneric(hdwf, secHoldOff) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHoldOffSet
                          )(hdwf, secHoldOff)
                return iretVal
            return WpFnGeneric(hdwf, secHoldOff)

        def WpDwfAnalogInTriggerHoldOffGet(self,
                                           hdwf : c_int,
                                           psecHoldOff : POINTER(c_double)
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
            def WpFnGeneric(hdwf, psecHoldOff) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHoldOffGet
                          )(hdwf, psecHoldOff)
                return iretVal
            return WpFnGeneric(hdwf, psecHoldOff)

        def WpDwfAnalogInTriggerTypeInfo(self,
                                         hdwf : c_int,
                                         pfstrigtype : POINTER(c_int)
                                         ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            use IsBitSet
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfstrigtype) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerTypeInfo
                          )(hdwf, pfstrigtype)
                return iretVal
            return WpFnGeneric(hdwf, pfstrigtype)

        def WpDwfAnalogInTriggerTypeSet(self,
                                        hdwf : c_int,
                                        trigtype : c_int
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
            def WpFnGeneric(hdwf, trigtype) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerTypeSet
                          )(hdwf, trigtype)
                return iretVal
            return WpFnGeneric(hdwf, trigtype)

        def WpDwfAnalogInTriggerTypeGet(self,
                                        hdwf : c_int,
                                        ptrigtype : POINTER(c_ubyte)
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
            def WpFnGeneric(hdwf, ptrigtype) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerTypeGet
                          )(hdwf, ptrigtype)
                return iretVal
            return WpFnGeneric(hdwf, ptrigtype)

        def WpDwfAnalogInTriggerChannelInfo(self,
                                            hdwf : c_int,
                                            pidxMin : POINTER(c_int),
                                            pidxMax : POINTER(c_int)
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
                       POINTER(c_int))
            def WpFnGeneric(hdwf, pidxMin, pidxMax) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerChannelInfo
                          )(hdwf, pidxMin, pidxMax)
                return iretVal
            return WpFnGeneric(hdwf, pidxMin, pidxMax)

        def WpDwfAnalogInTriggerChannelSet(self,
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
            @CFUNCTYPE(c_int, c_int)
            def WpFnGeneric(hdwf, idxChannel) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerChannelSet
                          )(hdwf, idxChannel)
                return iretVal
            return WpFnGeneric(hdwf, idxChannel)

        def WpDwfAnalogInTriggerChannelGet(self,
                                           hdwf : c_int,
                                           pidxChannel : POINTER(c_int)
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            """
            @CFUNCTYPE(c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pidxChannel) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerChannelGet
                          )(hdwf, pidxChannel)
                return iretVal
            return WpFnGeneric(hdwf, pidxChannel)

        def WpDwfAnalogInTriggerFilterInfo(self,
                                           hdwf : c_int,
                                           pfsfilter : POINTER(c_int)
                                           ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            use IsBitSet
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfsfilter) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerFilterInfo
                          )(hdwf, pfsfilter)
                return iretVal
            return WpFnGeneric(hdwf, pfsfilter)

        def WpDwfAnalogInTriggerFilterSet(self,
                                          hdwf : c_int,
                                          filter : c_int
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
            def WpFnGeneric(hdwf, filter) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerFilterSet
                          )(hdwf, filter)
                return iretVal
            return WpFnGeneric(hdwf, filter)

        def WpDwfAnalogInTriggerFilterGet(self,
                                          hdwf : c_int,
                                          pfilter : POINTER(c_int)
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
            def WpFnGeneric(hdwf, pfilter) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerFilterGet
                          )(hdwf, pfilter)
                return iretVal
            return WpFnGeneric(hdwf, pfilter)

        def WpDwfAnalogInTriggerLevelInfo(self,
                                          hdwf : c_int,
                                          pvoltsMin : POINTER(c_double),
                                          pvoltsMax : POINTER(c_double),
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
            def WpFnGeneric(hdwf, pvoltsMin, pvoltsMax, pnSteps) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLevelInfo
                          )(hdwf, pvoltsMin, pvoltsMax,
                            pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, pvoltsMin, pvoltsMax,
                               pnSteps)

        def WpDwfAnalogInTriggerLevelSet(self,
                                         hdwf : c_int,
                                         voltsLevel : c_double
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
            def WpFnGeneric(hdwf, voltsLevel) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLevelSet
                          )(hdwf, voltsLevel)
                return iretVal
            return WpFnGeneric(hdwf, voltsLevel)

        def WpDwfAnalogInTriggerLevelGet(self,
                                         hdwf : c_int,
                                         pvoltsLevel : POINTER(c_double)
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
            def WpFnGeneric(hdwf, pvoltsLevel) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLevelGet
                          )(hdwf, pvoltsLevel)
                return iretVal
            return WpFnGeneric(hdwf, pvoltsLevel)

        def WpDwfAnalogInTriggerHysteresisInfo(self,
                                               hdwf : c_int,
                                               pvoltsMin : POINTER(c_double),
                                               pvoltsMax : POINTER(c_double),
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
            def WpFnGeneric(hdwf, pvoltsMin, pvoltsMax, pnSteps) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHysteresisInfo
                          )(hdwf, pvoltsMin, pvoltsMax,
                            pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, pvoltsMin, pvoltsMax,
                               pnSteps)

        def WpDwfAnalogInTriggerHysteresisSet(self,
                                              hdwf : c_int,
                                              voltsLevel : c_double
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
            def WpFnGeneric(hdwf, voltsLevel) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHysteresisSet
                          )(hdwf, voltsLevel)
                return iretVal
            return WpFnGeneric(hdwf, voltsLevel)

        def WpDwfAnalogInTriggerHysteresisGet(self,
                                              hdwf : c_int,
                                              pvoltsHysteresis : POINTER(c_double)
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
            def WpFnGeneric(hdwf, pvoltsHysteresis) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerHysteresisGet
                          )(hdwf, pvoltsHysteresis)
                return iretVal
            return WpFnGeneric(hdwf, pvoltsHysteresis)

        def WpDwfAnalogInTriggerConditionInfo(self,
                                              hdwf : c_int,
                                              pfstrigcond : POINTER(c_int)
                                              ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            use IsBitSet
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfstrigcond) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerConditionInfo
                          )(hdwf, pfstrigcond)
                return iretVal
            return WpFnGeneric(hdwf, pfstrigcond)

        def WpDwfAnalogInTriggerConditionSet(self,
                                             hdwf : c_int,
                                             trigcond : c_int
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
            def WpFnGeneric(hdwf, trigcond) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerConditionSet
                          )(hdwf, trigcond)
                return iretVal
            return WpFnGeneric(hdwf, trigcond)

        def WpDwfAnalogInTriggerConditionGet(self,
                                             hdwf : c_int,
                                             ptrigcond : POINTER(c_int)
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
            def WpFnGeneric(hdwf, ptrigcond) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerConditionGet
                          )(hdwf, ptrigcond)
                return iretVal
            return WpFnGeneric(hdwf, ptrigcond)

        def WpDwfAnalogInTriggerLengthInfo(self,
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
            def WpFnGeneric(hdwf, psecMin, psecMax, pnSteps) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthInfo
                          )(hdwf, psecMin, psecMax, pnSteps)
                return iretVal
            return WpFnGeneric(hdwf, psecMin, psecMax, pnSteps)

        def WpDwfAnalogInTriggerLengthSet(self,
                                          hdwf : c_int,
                                          secLength : c_double
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
            def WpFnGeneric(hdwf, secLength) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthSet
                          )(hdwf, secLength)
                return iretVal
            return WpFnGeneric(hdwf, secLength)

        def WpDwfAnalogInTriggerLengthGet(self,
                                          hdwf : c_int,
                                          psecLength : POINTER(c_double)
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
            def WpFnGeneric(hdwf, psecLength) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthGet
                          )(hdwf, psecLength)
                return iretVal
            return WpFnGeneric(hdwf, psecLength)

        def WpDwfAnalogInTriggerLengthConditionInfo(self,
                                                    hdwf : c_int,
                                                    pfstriglen : POINTER(c_int)
                                                    ) -> int:
            """
            @Description
            @Parameters
            @Return
            0 or 1, False or True, True/1 is returned in case
            of correct behavior.
            @Notes
            use IsBitSet
            """
            @CFUNCTYPE(c_int, c_int, POINTER(c_int))
            def WpFnGeneric(hdwf, pfstriglen) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthConditionInfo
                          )(hdwf, pfstriglen)
                return iretVal
            return WpFnGeneric(hdwf, pfstriglen)

        def WpDwfAnalogInTriggerLengthConditionSet(self,
                                                   hdwf : c_int,
                                                   triglen : c_int
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
            def WpFnGeneric(hdwf, triglen) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthConditionSet
                          )(hdwf, triglen)
                return iretVal
            return WpFnGeneric(hdwf, triglen)

        def WpDwfAnalogInTriggerLengthConditionGet(self,
                                                   hdwf : c_int,
                                                   ptriglen : POINTER(c_int)
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
            def WpFnGeneric(hdwf, ptriglen) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInTriggerLengthConditionGet
                          )(hdwf, ptriglen)
                return iretVal
            return WpFnGeneric(hdwf, ptriglen)

        def WpDwfAnalogInSamplingSourceSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingSourceSet
                          )(hdwf, trigsrc)
                return iretVal
            return WpFnGeneric(hdwf, trigsrc)

        def WpDwfAnalogInSamplingSourceGet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingSourceGet
                          )(hdwf, ptrigsrc)
                return iretVal
            return WpFnGeneric(hdwf, ptrigsrc)

        def WpDwfAnalogInSamplingSlopeSet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingSlopeSet
                          )(hdwf, slope)
                return iretVal
            return WpFnGeneric(hdwf, slope)

        def WpDwfAnalogInSamplingSlopeGet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingSlopeGet
                          )(hdwf, pslope)
                return iretVal
            return WpFnGeneric(hdwf, pslope)

        def WpDwfAnalogInSamplingDelaySet(self,
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
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingDelaySet
                          )(hdwf, sec)
                return iretVal
            return WpFnGeneric(hdwf, sec)

        def WpDwfAnalogInSamplingDelayGet(self,
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
            @CFUNCTYPE(c_int, c_int, POINTER(c_double))
            def WpFnGeneric(hdwf, psec) -> int:
                iretVal = self.dtFuncOsc.get(
                            DwfFuncCorrelationAnalog.cFDwfAnalogInSamplingDelayGet
                          )(hdwf, psec)
                return iretVal
            return WpFnGeneric(hdwf, psec)
