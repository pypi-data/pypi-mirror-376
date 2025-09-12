
# Stdlib files
from enum import Enum, unique, auto

@unique
class DwfFuncCorrelationDevice(Enum):
    """
    @Description
    This class stores constants which are linked
    to functions inside dwf library. This approach
    is only for modularity, because some configurations
    need extra code added to get the expected behaviour.
    @Notes
    Mainly for device functions
    """

    ##################
    ## Enum & Param ##
    ##################

    # Default in 1, std lib defined
    # (maybe override _generate_next_value_() from enum.py)
    # Device Enumeration
    cFDwfParamSet = auto()
    cFDwfParamGet = auto()
    cFDwfEnum = auto()
    cFDwfEnumStart = auto()
    cFDwfEnumStop = auto()
    cFDwfEnumInfo = auto()
    cFDwfEnumDeviceType = auto()
    cFDwfEnumDeviceIsOpened = auto()
    cFDwfEnumUserName = auto()
    cFDwfEnumDeviceName = auto()
    cFDwfEnumSN = auto()
    cFDwfEnumConfig = auto()
    cFDwfEnumConfigInfo = auto()

    ################
    ## Device Cfg ##
    ################

    # Device Control
    cFDwfDeviceOpen = auto()
    cFDwfDeviceOpenEx = auto()
    cFDwfDeviceConfigOpen = auto()
    cFDwfDeviceClose = auto()
    cFDwfDeviceCloseAll = auto()
    cFDwfDeviceAutoConfigureSet = auto()
    cFDwfDeviceAutoConfigureGet = auto()
    cFDwfDeviceReset = auto()
    cFDwfDeviceEnableSet = auto()
    cFDwfDeviceTriggerInfo = auto()
    cFDwfDeviceTriggerSet = auto()
    cFDwfDeviceTriggerGet = auto()
    cFDwfDeviceTriggerPC = auto()
    cFDwfDeviceTriggerSlopeInfo = auto()
    cFDwfDeviceParamSet = auto()
    cFDwfDeviceParamGet = auto()

    #####################
    ## Runtime Getters ##
    #####################

    cFDwfGetLastError = auto()
    cFDwfGetLastErrorMsg = auto()
    cFDwfGetVersion = auto()

@unique
class DwfFuncCorrelationAnalog(Enum):
    """
    @Description
    This class stores constants which are linked 
    to functions inside dwf library. This approach 
    is only for modularity, because some configurations 
    need extra code added to get the expected behaviour.
    @Notes
    Generic, for analog instruments
    even if setters/getters are involved
    """

    ##################
    ## Oscilloscope ##
    ##################

    # Control and status
    cFDwfAnalogInReset = auto()
    cFDwfAnalogInConfigure = auto()
    cFDwfAnalogInTriggerForce = auto()
    cFDwfAnalogInStatus = auto()
    cFDwfAnalogInStatusSamplesLeft = auto()
    cFDwfAnalogInStatusSamplesValid = auto()
    cFDwfAnalogInStatusIndexWrite = auto()
    cFDwfAnalogInStatusAutoTriggered = auto()
    cFDwfAnalogInStatusData = auto()
    cFDwfAnalogInStatusData2 = auto()
    cFDwfAnalogInStatusData16 = auto()
    cFDwfAnalogInStatusDataMix16 = auto()
    cFDwfAnalogInStatusNoise = auto()
    cFDwfAnalogInStatusNoise2 = auto()
    cFDwfAnalogInStatusSample = auto()
    cFDwfAnalogInStatusTime = auto()
    cFDwfAnalogInStatusRecord = auto()
    cFDwfAnalogInRecordLengthSet = auto()
    cFDwfAnalogInRecordLengthGet = auto()
    cFDwfAnalogInCounterInfo = auto()
    cFDwfAnalogInCounterSet = auto()
    cFDwfAnalogInCounterGet = auto()
    cFDwfAnalogInCounterStatus = auto()

    # Acquisition configuration
    cFDwfAnalogInFrequencyInfo = auto()
    cFDwfAnalogInFrequencySet = auto()
    cFDwfAnalogInFrequencyGet = auto()
    cFDwfAnalogInBitsInfo = auto()
    cFDwfAnalogInBufferSizeInfo = auto()
    cFDwfAnalogInBufferSizeSet = auto()
    cFDwfAnalogInBufferSizeGet = auto()
    cFDwfAnalogInBuffersInfo = auto()
    cFDwfAnalogInBuffersSet = auto()
    cFDwfAnalogInBuffersGet = auto()
    cFDwfAnalogInBuffersStatus = auto()
    cFDwfAnalogInNoiseSizeInfo = auto()
    cFDwfAnalogInNoiseSizeSet = auto()
    cFDwfAnalogInNoiseSizeGet = auto()
    cFDwfAnalogInAcquisitionModeInfo = auto()
    cFDwfAnalogInAcquisitionModeSet = auto()
    cFDwfAnalogInAcquisitionModeGet = auto()

    # Channel configuration
    cFDwfAnalogInChannelCount = auto()
    cFDwfAnalogInChannelCounts = auto()
    cFDwfAnalogInChannelEnableSet = auto()
    cFDwfAnalogInChannelEnableGet = auto()
    cFDwfAnalogInChannelFilterInfo = auto()
    cFDwfAnalogInChannelFilterSet = auto()
    cFDwfAnalogInChannelFilterGet = auto()
    cFDwfAnalogInChannelRangeInfo = auto()
    cFDwfAnalogInChannelRangeSteps = auto()
    cFDwfAnalogInChannelRangeSet = auto()
    cFDwfAnalogInChannelRangeGet = auto()
    cFDwfAnalogInChannelOffsetInfo = auto()
    cFDwfAnalogInChannelOffsetSet = auto()
    cFDwfAnalogInChannelOffsetGet = auto()
    cFDwfAnalogInChannelAttenuationSet = auto()
    cFDwfAnalogInChannelAttenuationGet = auto()
    cFDwfAnalogInChannelBandwidthSet = auto()
    cFDwfAnalogInChannelBandwidthGet = auto()
    cFDwfAnalogInChannelImpedanceSet = auto()
    cFDwfAnalogInChannelImpedanceGet = auto()
    cFDwfAnalogInChannelCouplingInfo = auto()
    cFDwfAnalogInChannelCouplingSet = auto()
    cFDwfAnalogInChannelCouplingGet = auto()

    # IIR filters
    cFDwfAnalogInChannelFiirInfo = auto()
    cFDwfAnalogInChannelFiirSet = auto()
    cFDwfAnalogInChannelWindowSet = auto()
    cFDwfAnalogInChannelCustomWindowSet = auto()

    # Trigger configuration
    cFDwfAnalogInTriggerSourceSet = auto()
    cFDwfAnalogInTriggerSourceGet = auto()
    cFDwfAnalogInTriggerPositionInfo = auto()
    cFDwfAnalogInTriggerPositionSet = auto()
    cFDwfAnalogInTriggerPositionGet = auto()
    cFDwfAnalogInTriggerPositionStatus = auto()
    cFDwfAnalogInTriggerAutoTimeoutInfo = auto()
    cFDwfAnalogInTriggerAutoTimeoutSet = auto()
    cFDwfAnalogInTriggerAutoTimeoutGet = auto()
    cFDwfAnalogInTriggerHoldOffInfo = auto()
    cFDwfAnalogInTriggerHoldOffSet = auto()
    cFDwfAnalogInTriggerHoldOffGet = auto()
    cFDwfAnalogInTriggerTypeInfo = auto()
    cFDwfAnalogInTriggerTypeSet = auto()
    cFDwfAnalogInTriggerTypeGet = auto()
    cFDwfAnalogInTriggerChannelInfo = auto()
    cFDwfAnalogInTriggerChannelSet = auto()
    cFDwfAnalogInTriggerChannelGet = auto()
    cFDwfAnalogInTriggerFilterInfo = auto()
    cFDwfAnalogInTriggerFilterSet = auto()
    cFDwfAnalogInTriggerFilterGet = auto()
    cFDwfAnalogInTriggerLevelInfo = auto()
    cFDwfAnalogInTriggerLevelSet = auto()
    cFDwfAnalogInTriggerLevelGet = auto()
    cFDwfAnalogInTriggerHysteresisInfo = auto()
    cFDwfAnalogInTriggerHysteresisSet = auto()
    cFDwfAnalogInTriggerHysteresisGet = auto()
    cFDwfAnalogInTriggerConditionInfo = auto()
    cFDwfAnalogInTriggerConditionSet = auto()
    cFDwfAnalogInTriggerConditionGet = auto()
    cFDwfAnalogInTriggerLengthInfo = auto()
    cFDwfAnalogInTriggerLengthSet = auto()
    cFDwfAnalogInTriggerLengthGet = auto()
    cFDwfAnalogInTriggerLengthConditionInfo = auto()
    cFDwfAnalogInTriggerLengthConditionSet = auto()
    cFDwfAnalogInTriggerLengthConditionGet = auto()
    cFDwfAnalogInSamplingSourceSet = auto()
    cFDwfAnalogInSamplingSourceGet = auto()
    cFDwfAnalogInSamplingSlopeSet = auto()
    cFDwfAnalogInSamplingSlopeGet = auto()
    cFDwfAnalogInSamplingDelaySet = auto()
    cFDwfAnalogInSamplingDelayGet = auto()

    ###############
    ##  WaveGen  ##
    ###############

    # Configuration
    cFDwfAnalogOutCount = auto()
    cFDwfAnalogOutMasterSet = auto()
    cFDwfAnalogOutMasterGet = auto()
    cFDwfAnalogOutTriggerSourceSet = auto()
    cFDwfAnalogOutTriggerSourceGet = auto()
    cFDwfAnalogOutTriggerSlopeSet = auto()
    cFDwfAnalogOutTriggerSlopeGet = auto()
    cFDwfAnalogOutRunInfo = auto()
    cFDwfAnalogOutRunSet = auto()
    cFDwfAnalogOutRunGet = auto()
    cFDwfAnalogOutRunStatus = auto()
    cFDwfAnalogOutWaitInfo = auto()
    cFDwfAnalogOutWaitSet = auto()
    cFDwfAnalogOutWaitGet = auto()
    cFDwfAnalogOutRepeatInfo = auto()
    cFDwfAnalogOutRepeatSet = auto()
    cFDwfAnalogOutRepeatGet = auto()
    cFDwfAnalogOutRepeatStatus = auto()    
    cFDwfAnalogOutRepeatTriggerSet = auto()
    cFDwfAnalogOutRepeatTriggerGet = auto()

    # EExplorer, DPS3340 channel 3&4 current/voltage limitation
    cFDwfAnalogOutLimitationInfo = auto()
    cFDwfAnalogOutLimitationSet = auto()
    cFDwfAnalogOutLimitationGet = auto()
    cFDwfAnalogOutModeSet = auto()
    cFDwfAnalogOutModeGet = auto() 
    cFDwfAnalogOutIdleInfo = auto()
    cFDwfAnalogOutIdleSet = auto()
    cFDwfAnalogOutIdleGet = auto()
    cFDwfAnalogOutNodeInfo = auto()

    # Mode: 0 Disable, 1 Enable
    # for FM node: 1 is Frequenc Modulation (+-200%),
    #              2 is Phase Modulation (+-100%),
    #              3 is PMD with degree (+-180%) amplitude/offset units
    # for AM node: 1 is Amplitude Modulation (+-200%),
    #              2 is SUM (+-400%),
    #              3 is SUM with Volts amplitude/offset units (+-4X CarrierAmplitude)
    # PID output: 4
    cFDwfAnalogOutNodeEnableSet = auto()
    cFDwfAnalogOutNodeEnableGet = auto()
    cFDwfAnalogOutNodeFunctionInfo = auto()
    cFDwfAnalogOutNodeFunctionSet = auto()
    cFDwfAnalogOutNodeFunctionGet = auto()
    cFDwfAnalogOutNodeFrequencyInfo = auto()
    cFDwfAnalogOutNodeFrequencySet = auto()
    cFDwfAnalogOutNodeFrequencyGet = auto()

    # Carrier Amplitude or Modulation Index
    cFDwfAnalogOutNodeAmplitudeInfo = auto()
    cFDwfAnalogOutNodeAmplitudeSet = auto()
    cFDwfAnalogOutNodeAmplitudeGet = auto()    
    cFDwfAnalogOutNodeOffsetInfo = auto()
    cFDwfAnalogOutNodeOffsetSet = auto()
    cFDwfAnalogOutNodeOffsetGet = auto()    
    cFDwfAnalogOutNodeSymmetryInfo = auto()
    cFDwfAnalogOutNodeSymmetrySet = auto()
    cFDwfAnalogOutNodeSymmetryGet = auto()
    cFDwfAnalogOutNodePhaseInfo = auto()
    cFDwfAnalogOutNodePhaseSet = auto()
    cFDwfAnalogOutNodePhaseGet = auto()
    cFDwfAnalogOutNodeDataInfo = auto()
    cFDwfAnalogOutNodeDataSet = auto()

    # Needed for EExplorer, not used for Analog Discovery
    cFDwfAnalogOutCustomAMFMEnableSet = auto()
    cFDwfAnalogOutCustomAMFMEnableGet = auto()

    # Control
    cFDwfAnalogOutReset = auto()
    cFDwfAnalogOutConfigure = auto()
    cFDwfAnalogOutStatus = auto()
    cFDwfAnalogOutNodePlayInfo = auto()
    cFDwfAnalogOutNodePlayStatus = auto()
    cFDwfAnalogOutNodePlayData = auto()

    #########
    ## I/O ##
    #########

    # Control
    cFDwfAnalogIOReset = auto()
    cFDwfAnalogIOConfigure = auto()
    cFDwfAnalogIOStatus = auto()

    # Configure
    cFDwfAnalogIOEnableInfo = auto()
    cFDwfAnalogIOEnableSet = auto()
    cFDwfAnalogIOEnableGet = auto()
    cFDwfAnalogIOEnableStatus = auto()
    cFDwfAnalogIOChannelCount = auto()
    cFDwfAnalogIOChannelName = auto()
    cFDwfAnalogIOChannelInfo = auto()
    cFDwfAnalogIOChannelNodeName = auto()
    cFDwfAnalogIOChannelNodeInfo = auto()
    cFDwfAnalogIOChannelNodeSetInfo = auto()
    cFDwfAnalogIOChannelNodeSet = auto()
    cFDwfAnalogIOChannelNodeGet = auto()
    cFDwfAnalogIOChannelNodeStatusInfo = auto()
    cFDwfAnalogIOChannelNodeStatus = auto()

    ###############
    ## Impedance ##
    ###############

    cFDwfAnalogImpedanceReset = auto()
    cFDwfAnalogImpedanceModeSet = auto()
    cFDwfAnalogImpedanceModeGet = auto()
    cFDwfAnalogImpedanceReferenceSet = auto()
    cFDwfAnalogImpedanceReferenceGet = auto()
    cFDwfAnalogImpedanceFrequencySet = auto()
    cFDwfAnalogImpedanceFrequencyGet = auto()
    cFDwfAnalogImpedanceAmplitudeSet = auto()
    cFDwfAnalogImpedanceAmplitudeGet = auto()
    cFDwfAnalogImpedanceOffsetSet = auto()
    cFDwfAnalogImpedanceOffsetGet = auto()
    cFDwfAnalogImpedanceProbeSet = auto()
    cFDwfAnalogImpedanceProbeGet = auto()
    cFDwfAnalogImpedancePeriodSet = auto()
    cFDwfAnalogImpedancePeriodGet = auto()
    cFDwfAnalogImpedanceCompReset = auto()
    cFDwfAnalogImpedanceCompSet = auto()
    cFDwfAnalogImpedanceCompGet = auto()
    cFDwfAnalogImpedanceConfigure = auto()
    cFDwfAnalogImpedanceStatus = auto()
    cFDwfAnalogImpedanceStatusInput = auto()
    cFDwfAnalogImpedanceStatusWarning = auto()
    cFDwfAnalogImpedanceStatusMeasure = auto()

    ############
    ## Others ##
    ############

    # use cFDwfDeviceTriggerInfo - ptrigsrcInfo
    cFDwfAnalogInTriggerSourceInfo = auto()
    cFDwfAnalogOutTriggerSourceInfo = auto()

    # use cFDwfAnalogOutNode...
    cFDwfAnalogOutEnableSet = auto()
    cFDwfAnalogOutEnableGet = auto()
    cFDwfAnalogOutFunctionInfo = auto()
    cFDwfAnalogOutFunctionSet = auto()
    cFDwfAnalogOutFunctionGet = auto()
    cFDwfAnalogOutFrequencyInfo = auto()
    cFDwfAnalogOutFrequencySet = auto()
    cFDwfAnalogOutFrequencyGet = auto()
    cFDwfAnalogOutAmplitudeInfo = auto()
    cFDwfAnalogOutAmplitudeSet = auto()
    cFDwfAnalogOutAmplitudeGet = auto()
    cFDwfAnalogOutOffsetInfo = auto()
    cFDwfAnalogOutOffsetSet = auto()
    cFDwfAnalogOutOffsetGet = auto()
    cFDwfAnalogOutSymmetryInfo = auto()
    cFDwfAnalogOutSymmetrySet = auto()
    cFDwfAnalogOutSymmetryGet = auto()
    cFDwfAnalogOutPhaseInfo = auto()
    cFDwfAnalogOutPhaseSet = auto()
    cFDwfAnalogOutPhaseGet = auto()
    cFDwfAnalogOutDataInfo = auto()
    cFDwfAnalogOutDataSet = auto()
    cFDwfAnalogOutPlayStatus = auto()
    cFDwfAnalogOutPlayData = auto()

    # use cFDwfAnalogInChannelCount
    cFDwfEnumAnalogInChannels = auto()
    # use cFDwfEnumConfigInfo
    cFDwfEnumAnalogInBufferSize = auto()
    # use cFDwfAnalogInBitsInfo
    cFDwfEnumAnalogInBits = auto()
    # use cFDwfEnumAnalogInFrequency
    cFDwfEnumAnalogInFrequency = auto()

@unique
class DwfFuncCorrelationDigital(Enum):
    """
    @Description
    This class stores constants which are linked 
    to functions inside dwf library. This approach 
    is only for modularity, because some configurations 
    need extra code added to get the expected behaviour.
    @Notes
    Generic, for digital instruments
    even if setters/getters are involved
    """

    #########
    ## I/O ##
    #########

    # Control
    cFDwfDigitalIOReset = auto()
    cFDwfDigitalIOConfigure = auto()
    cFDwfDigitalIOStatus = auto()

    # Configure
    cFDwfDigitalIOOutputEnableInfo = auto()
    cFDwfDigitalIOOutputEnableSet = auto()
    cFDwfDigitalIOOutputEnableGet = auto()
    cFDwfDigitalIOOutputInfo = auto()
    cFDwfDigitalIOOutputSet = auto()
    cFDwfDigitalIOOutputGet = auto()
    cFDwfDigitalIOPullInfo = auto()
    cFDwfDigitalIOPullSet = auto()
    cFDwfDigitalIOPullGet = auto()
    cFDwfDigitalIODriveInfo = auto()
    cFDwfDigitalIODriveSet = auto()
    cFDwfDigitalIODriveGet = auto()
    cFDwfDigitalIOInputInfo = auto()
    cFDwfDigitalIOInputStatus = auto()
    cFDwfDigitalIOOutputEnableInfo64 = auto()
    cFDwfDigitalIOOutputEnableSet64 = auto()
    cFDwfDigitalIOOutputEnableGet64 = auto()
    cFDwfDigitalIOOutputInfo64 = auto()
    cFDwfDigitalIOOutputSet64 = auto()
    cFDwfDigitalIOOutputGet64 = auto()
    cFDwfDigitalIOInputInfo64 = auto()
    cFDwfDigitalIOInputStatus64 = auto()

    ####################
    ## Logic Analyzer ##
    ####################

    # Control and status
    cFDwfDigitalInReset = auto()
    cFDwfDigitalInConfigure = auto()
    cFDwfDigitalInStatus = auto()
    cFDwfDigitalInStatusSamplesLeft = auto()
    cFDwfDigitalInStatusSamplesValid = auto()
    cFDwfDigitalInStatusIndexWrite = auto()
    cFDwfDigitalInStatusAutoTriggered = auto()
    cFDwfDigitalInStatusData = auto()
    cFDwfDigitalInStatusData2 = auto()
    cFDwfDigitalInStatusData3 = auto()
    cFDwfDigitalInStatusNoise2 = auto()
    cFDwfDigitalInStatusNoise3 = auto()
    cFDwfDigitalInStatusRecord = auto()
    cFDwfDigitalInStatusCompress = auto()
    cFDwfDigitalInStatusCompressed = auto()
    cFDwfDigitalInStatusCompressed2 = auto()
    cFDwfDigitalInStatusTime = auto()
    cFDwfDigitalInCounterInfo = auto()
    cFDwfDigitalInCounterSet = auto()
    cFDwfDigitalInCounterGet = auto()
    cFDwfDigitalInCounterStatus = auto()

    # Acquisition configuration
    cFDwfDigitalInInternalClockInfo = auto()
    cFDwfDigitalInClockSourceInfo = auto()
    cFDwfDigitalInClockSourceSet = auto()
    cFDwfDigitalInClockSourceGet = auto()
    cFDwfDigitalInDividerInfo = auto()
    cFDwfDigitalInDividerSet = auto()
    cFDwfDigitalInDividerGet = auto()
    cFDwfDigitalInBitsInfo = auto()
    cFDwfDigitalInSampleFormatSet = auto()
    cFDwfDigitalInSampleFormatGet = auto()
    cFDwfDigitalInInputOrderSet = auto()
    cFDwfDigitalInBufferSizeInfo = auto()
    cFDwfDigitalInBufferSizeSet = auto()
    cFDwfDigitalInBufferSizeGet = auto()
    cFDwfDigitalInBuffersInfo = auto()
    cFDwfDigitalInBuffersSet = auto()
    cFDwfDigitalInBuffersGet = auto()
    cFDwfDigitalInBuffersStatus = auto()
    cFDwfDigitalInSampleModeInfo = auto()
    cFDwfDigitalInSampleModeSet = auto()
    cFDwfDigitalInSampleModeGet = auto()
    cFDwfDigitalInSampleSensibleSet = auto()
    cFDwfDigitalInSampleSensibleGet = auto()
    cFDwfDigitalInAcquisitionModeInfo = auto()
    cFDwfDigitalInAcquisitionModeSet = auto()
    cFDwfDigitalInAcquisitionModeGet = auto()

    # Trigger configuration
    cFDwfDigitalInTriggerSourceSet = auto()
    cFDwfDigitalInTriggerSourceGet = auto()
    cFDwfDigitalInTriggerSlopeSet = auto()
    cFDwfDigitalInTriggerSlopeGet = auto()
    cFDwfDigitalInTriggerPositionInfo = auto()
    cFDwfDigitalInTriggerPositionSet = auto()
    cFDwfDigitalInTriggerPositionGet = auto()
    cFDwfDigitalInTriggerPrefillSet = auto()
    cFDwfDigitalInTriggerPrefillGet = auto()
    cFDwfDigitalInTriggerAutoTimeoutInfo = auto()
    cFDwfDigitalInTriggerAutoTimeoutSet = auto()
    cFDwfDigitalInTriggerAutoTimeoutGet = auto()
    cFDwfDigitalInTriggerInfo = auto()
    cFDwfDigitalInTriggerSet = auto()
    cFDwfDigitalInTriggerGet = auto()
    cFDwfDigitalInTriggerInfo64 = auto()
    cFDwfDigitalInTriggerSet64 = auto()
    cFDwfDigitalInTriggerGet64 = auto()

    # The logic for trigger bits: Low and High and (Rise or Fall)
    # Bits set in Rise and Fall means any edge
    cFDwfDigitalInTriggerResetSet = auto()
    cFDwfDigitalInTriggerResetSet64 = auto()
    cFDwfDigitalInTriggerCountSet = auto()
    cFDwfDigitalInTriggerLengthSet = auto()
    cFDwfDigitalInTriggerMatchSet = auto()

    ################
    ## PatternGen ##
    ################

    # Control
    cFDwfDigitalOutReset = auto()
    cFDwfDigitalOutConfigure = auto()
    cFDwfDigitalOutStatus = auto()
    cFDwfDigitalOutStatusOutput = auto()

    # Configuration
    cFDwfDigitalOutInternalClockInfo = auto()
    cFDwfDigitalOutTriggerSourceSet = auto()
    cFDwfDigitalOutTriggerSourceGet = auto()
    cFDwfDigitalOutRunInfo = auto()
    cFDwfDigitalOutRunSet = auto()
    cFDwfDigitalOutRunGet = auto()
    cFDwfDigitalOutRunStatus = auto()
    cFDwfDigitalOutWaitInfo = auto()
    cFDwfDigitalOutWaitSet = auto()
    cFDwfDigitalOutWaitGet = auto()
    cFDwfDigitalOutRepeatInfo = auto()
    cFDwfDigitalOutRepeatSet = auto()
    cFDwfDigitalOutRepeatGet = auto()
    cFDwfDigitalOutRepeatStatus = auto()
    cFDwfDigitalOutTriggerSlopeSet = auto()
    cFDwfDigitalOutTriggerSlopeGet = auto()
    cFDwfDigitalOutRepeatTriggerSet = auto()
    cFDwfDigitalOutRepeatTriggerGet = auto()
    cFDwfDigitalOutCount = auto()
    cFDwfDigitalOutEnableSet = auto()
    cFDwfDigitalOutEnableGet = auto()
    cFDwfDigitalOutOutputInfo = auto()
    cFDwfDigitalOutOutputSet = auto()
    cFDwfDigitalOutOutputGet = auto()
    cFDwfDigitalOutTypeInfo = auto()
    cFDwfDigitalOutTypeSet = auto()
    cFDwfDigitalOutTypeGet = auto()
    cFDwfDigitalOutIdleInfo = auto()
    cFDwfDigitalOutIdleSet = auto()
    cFDwfDigitalOutIdleGet = auto()
    cFDwfDigitalOutDividerInfo = auto()
    cFDwfDigitalOutDividerInitSet = auto()
    cFDwfDigitalOutDividerInitGet = auto()
    cFDwfDigitalOutDividerSet = auto()
    cFDwfDigitalOutDividerGet = auto()
    cFDwfDigitalOutCounterInfo = auto()
    cFDwfDigitalOutCounterInitSet = auto()
    cFDwfDigitalOutCounterInitGet = auto()
    cFDwfDigitalOutCounterSet = auto()
    cFDwfDigitalOutCounterGet = auto()

    # ADP3X50
    cFDwfDigitalOutRepetitionInfo = auto()
    cFDwfDigitalOutRepetitionSet = auto()
    cFDwfDigitalOutRepetitionGet = auto()

    # For all boards
    cFDwfDigitalOutDataInfo = auto()
    cFDwfDigitalOutDataSet = auto()
    cFDwfDigitalOutPlayDataSet = auto()
    cFDwfDigitalOutPlayUpdateSet = auto()
    cFDwfDigitalOutPlayRateSet = auto()

    # UART
    cFDwfDigitalUartReset = auto()
    cFDwfDigitalUartRateSet = auto()
    cFDwfDigitalUartBitsSet = auto()
    cFDwfDigitalUartParitySet = auto()
    cFDwfDigitalUartPolaritySet = auto()
    cFDwfDigitalUartStopSet = auto()
    cFDwfDigitalUartTxSet = auto()
    cFDwfDigitalUartRxSet = auto()
    cFDwfDigitalUartTx = auto()
    cFDwfDigitalUartRx = auto()

    # SPI
    cFDwfDigitalSpiReset = auto()
    cFDwfDigitalSpiFrequencySet = auto()
    cFDwfDigitalSpiClockSet = auto()
    cFDwfDigitalSpiDataSet = auto()
    cFDwfDigitalSpiIdleSet = auto()
    cFDwfDigitalSpiModeSet = auto()
    cFDwfDigitalSpiOrderSet = auto()
    cFDwfDigitalSpiDelaySet = auto()
    cFDwfDigitalSpiSelectSet = auto()
    cFDwfDigitalSpiSelect = auto()
    cFDwfDigitalSpiWriteRead = auto()
    cFDwfDigitalSpiWriteRead16 = auto()
    cFDwfDigitalSpiWriteRead32 = auto()
    cFDwfDigitalSpiRead = auto()
    cFDwfDigitalSpiReadOne = auto()
    cFDwfDigitalSpiRead16 = auto()
    cFDwfDigitalSpiRead32 = auto()
    cFDwfDigitalSpiWrite = auto()
    cFDwfDigitalSpiWriteOne = auto()
    cFDwfDigitalSpiWrite16 = auto()
    cFDwfDigitalSpiWrite32 = auto()
    cFDwfDigitalSpiCmdWriteRead = auto()
    cFDwfDigitalSpiCmdWriteRead16 = auto()
    cFDwfDigitalSpiCmdWriteRead32 = auto()
    cFDwfDigitalSpiCmdRead = auto()
    cFDwfDigitalSpiCmdReadOne = auto()
    cFDwfDigitalSpiCmdRead16 = auto()
    cFDwfDigitalSpiCmdRead32 = auto()
    cFDwfDigitalSpiCmdWrite = auto()
    cFDwfDigitalSpiCmdWriteOne = auto()
    cFDwfDigitalSpiCmdWrite16 = auto()
    cFDwfDigitalSpiCmdWrite32 = auto()

    # I2C
    cFDwfDigitalI2cReset = auto()
    cFDwfDigitalI2cClear = auto()
    cFDwfDigitalI2cStretchSet = auto()
    cFDwfDigitalI2cRateSet = auto()
    cFDwfDigitalI2cReadNakSet = auto()
    cFDwfDigitalI2cSclSet = auto()
    cFDwfDigitalI2cSdaSet = auto()
    cFDwfDigitalI2cTimeoutSet = auto()
    cFDwfDigitalI2cWriteRead = auto()
    cFDwfDigitalI2cRead = auto()
    cFDwfDigitalI2cWrite = auto()
    cFDwfDigitalI2cWriteOne = auto()
    cFDwfDigitalI2cSpyStart = auto()
    cFDwfDigitalI2cSpyStatus = auto()

    # CAN
    cFDwfDigitalCanReset = auto()
    cFDwfDigitalCanRateSet = auto()
    cFDwfDigitalCanPolaritySet = auto()
    cFDwfDigitalCanTxSet = auto()
    cFDwfDigitalCanRxSet = auto()
    cFDwfDigitalCanTx = auto()
    cFDwfDigitalCanRx = auto()

    # SWD
    cFDwfDigitalSwdReset = auto()
    cFDwfDigitalSwdRateSet = auto()
    cFDwfDigitalSwdCkSet = auto()
    cFDwfDigitalSwdIoSet = auto()
    cFDwfDigitalSwdTurnSet = auto()
    cFDwfDigitalSwdTrailSet = auto()
    cFDwfDigitalSwdParkSet = auto()
    cFDwfDigitalSwdNakSet = auto()
    cFDwfDigitalSwdIoIdleSet = auto()
    cFDwfDigitalSwdClear = auto()
    cFDwfDigitalSwdWrite = auto()
    cFDwfDigitalSwdRead = auto()

    ############
    ## Others ##
    ############

    # use cFDwfDigitalInTriggerSourceSet - trigsrcAnalogIn
    # call cFDwfDigitalInConfigure before cFDwfAnalogInConfigure
    cFDwfDigitalInMixedSet = auto()
    # use cFDwfDeviceTriggerInfo - ptrigsrcInfo
    cFDwfDigitalInTriggerSourceInfo = auto()
    cFDwfDigitalOutTriggerSourceInfo = auto()

@unique
class DwfFuncCorrelationMisc(Enum):
    """
    @Description
    This class stores constants which are linked 
    to functions inside dwf library. This approach 
    is only for modularity, because some configurations 
    need extra code added to get the expected behaviour.
    @Notes
    Extra functionalities for filtering cases
    """

    ###################
    ## Miscellaneous ##
    ###################

    cFDwfSpectrumWindow = auto()
    cFDwfSpectrumFFT = auto()
    cFDwfSpectrumTransform = auto()
    cFDwfSpectrumGoertzel = auto()
