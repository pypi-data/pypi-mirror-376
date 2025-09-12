
# Stdlib file(s)
from ctypes import c_int, c_ubyte

class DwfSymbolsConstants:
    """
    @Description
    This class consists of symbol related
    constants mainly to be accessed by dwf lib
    functions for device configs, instruments.
    """
    
    ############################################################
    ### Symbols intended for local use only, not by dwf lib. ###
    ############################################################
    
    WP_DWFERROR = 0
    WP_DWFSUCCESS = 1 # 1 for Dwf functions
    
    #######################################################
    ### From dwf.h file installed along with waveforms, ###
    ### with compatibility between Py and C.            ###
    #######################################################
    
    # device handle
    hdwfNone = c_int(0)
    
    # device enumeration filters
    enumfilterAll = c_int(0)
    enumfilterType = c_int(0x8000000)
    enumfilterUSB = c_int(0x0000001)
    enumfilterNetwork = c_int(0x0000002)
    enumfilterAXI = c_int(0x0000004)
    enumfilterRemote = c_int(0x1000000)
    enumfilterAudio = c_int(0x2000000)
    enumfilterDemo = c_int(0x4000000)
    
    # device ID
    devidEExplorer = c_int(1)
    devidDiscovery = c_int(2)
    devidDiscovery2 = c_int(3)
    devidDDiscovery = c_int(4)
    devidADP3X50 = c_int(6)
    devidEclypse = c_int(7)
    devidADP5250 = c_int(8)
    devidDPS3340 = c_int(9)
    devidDiscovery3 = c_int(10)
    devidADP5470 = c_int(11)
    devidADP5490 = c_int(12)
    devidADP2230 = c_int(14)
    
    # device version
    devverEExplorerC = c_int(2)
    devverEExplorerE = c_int(4)
    devverEExplorerF = c_int(5)
    devverDiscoveryA = c_int(1)
    devverDiscoveryB = c_int(2)
    devverDiscoveryC = c_int(3)
    
    # trigger source
    trigsrcNone = c_ubyte(0)
    trigsrcPC = c_ubyte(1)
    trigsrcDetectorAnalogIn = c_ubyte(2)
    trigsrcDetectorDigitalIn = c_ubyte(3)
    trigsrcAnalogIn = c_ubyte(4)
    trigsrcDigitalIn = c_ubyte(5)
    trigsrcDigitalOut = c_ubyte(6)
    trigsrcAnalogOut1 = c_ubyte(7)
    trigsrcAnalogOut2 = c_ubyte(8)
    trigsrcAnalogOut3 = c_ubyte(9)
    trigsrcAnalogOut4 = c_ubyte(10)
    trigsrcExternal1 = c_ubyte(11)
    trigsrcExternal2 = c_ubyte(12)
    trigsrcExternal3 = c_ubyte(13)
    trigsrcExternal4 = c_ubyte(14)
    trigsrcHigh = c_ubyte(15)
    trigsrcLow = c_ubyte(16)
    trigsrcClock = c_ubyte(17)
    
    # instrument states:
    DwfStateReady = c_ubyte(0)
    DwfStateConfig = c_ubyte(4)
    DwfStatePrefill = c_ubyte(5)
    DwfStateArmed = c_ubyte(1)
    DwfStateWait = c_ubyte(7)
    DwfStateTriggered = c_ubyte(3)
    DwfStateRunning = c_ubyte(3)
    DwfStateDone = c_ubyte(2)
    DwfStateNotDone = c_ubyte(6)
    
    DECIAnalogInChannelCount = c_int(1)
    DECIAnalogOutChannelCount = c_int(2)
    DECIAnalogIOChannelCount = c_int(3)
    DECIDigitalInChannelCount = c_int(4)
    DECIDigitalOutChannelCount = c_int(5)
    DECIDigitalIOChannelCount = c_int(6)
    DECIAnalogInBufferSize = c_int(7)
    DECIAnalogOutBufferSize = c_int(8)
    DECIDigitalInBufferSize = c_int(9)
    DECIDigitalOutBufferSize = c_int(10)
    DECIPowerOutChannelCount = c_int(11)
    DECIPowerOutBufferSize = c_int(12)
    DECIAnalogOutPlaySize = c_int(13)
    
    # acquisition modes:
    acqmodeSingle = c_int(0)
    acqmodeScanShift = c_int(1)
    acqmodeScanScreen = c_int(2)
    acqmodeRecord = c_int(3)
    acqmodeOvers = c_int(4)
    acqmodeSingle1 = c_int(5)
    
    # analog acquisition filter:
    filterDecimate = c_int(0)
    filterAverage = c_int(1)
    filterMinMax = c_int(2)
    filterAverageFit = c_int(3)
    
    # analog in trigger mode:
    trigtypeEdge = c_int(0)
    trigtypePulse = c_int(1)
    trigtypeTransition = c_int(2)
    trigtypeWindow = c_int(3)
    
    # trigger slope:
    DwfTriggerSlopeRise = c_int(0)
    DwfTriggerSlopeFall = c_int(1)
    DwfTriggerSlopeEither = c_int(2)
    
    # trigger length condition
    triglenLess = c_int(0)
    triglenTimeout = c_int(1)
    triglenMore = c_int(2)
    
    # error codes for the functions:
    dwfercNoErc = c_int(0)                #  No error occurred
    dwfercUnknownError = c_int(1)         #  API waiting on pending API timed out
    dwfercApiLockTimeout = c_int(2)       #  API waiting on pending API timed out
    dwfercAlreadyOpened = c_int(3)        #  Device already opened
    dwfercNotSupported = c_int(4)         #  Device not supported
    dwfercInvalidParameter0 = c_int(0x10) #  Invalid parameter sent in API call
    dwfercInvalidParameter1 = c_int(0x11) #  Invalid parameter sent in API call
    dwfercInvalidParameter2 = c_int(0x12) #  Invalid parameter sent in API call
    dwfercInvalidParameter3 = c_int(0x13) #  Invalid parameter sent in API call
    dwfercInvalidParameter4 = c_int(0x14) #  Invalid parameter sent in API call
    
    # analog out signal types
    funcDC = c_ubyte(0)
    funcSine = c_ubyte(1)
    funcSquare = c_ubyte(2)
    funcTriangle = c_ubyte(3)
    funcRampUp = c_ubyte(4)
    funcRampDown = c_ubyte(5)
    funcNoise = c_ubyte(6)
    funcPulse = c_ubyte(7)
    funcTrapezium = c_ubyte(8)
    funcSinePower = c_ubyte(9)
    funcSineNA = c_ubyte(10)
    funcCustomPattern = c_ubyte(28)
    funcPlayPattern = c_ubyte(29)
    funcCustom = c_ubyte(30)
    funcPlay = c_ubyte(31)
    
    funcAnalogIn1 = c_ubyte(64)
    funcAnalogIn2 = c_ubyte(65)
    funcAnalogIn3 = c_ubyte(66)
    funcAnalogIn4 = c_ubyte(67)
    funcAnalogIn5 = c_ubyte(68)
    funcAnalogIn6 = c_ubyte(69)
    funcAnalogIn7 = c_ubyte(70)
    funcAnalogIn8 = c_ubyte(71)
    funcAnalogIn9 = c_ubyte(72)
    funcAnalogIn10 = c_ubyte(73)
    funcAnalogIn11 = c_ubyte(74)
    funcAnalogIn12 = c_ubyte(75)
    funcAnalogIn13 = c_ubyte(76)
    funcAnalogIn14 = c_ubyte(77)
    funcAnalogIn15 = c_ubyte(78)
    funcAnalogIn16 = c_ubyte(79)
    
    # analog io channel node types
    analogioEnable = c_ubyte(1)
    analogioVoltage = c_ubyte(2)
    analogioCurrent = c_ubyte(3)
    analogioPower = c_ubyte(4)
    analogioTemperature = c_ubyte(5)
    analogioDmm = c_ubyte(6)
    analogioRange = c_ubyte(7)
    analogioMeasure = c_ubyte(8)
    analogioTime = c_ubyte(9)
    analogioFrequency = c_ubyte(10)
    analogioResistance = c_ubyte(11)
    analogioSlew = c_ubyte(12)
    
    DwfDmmResistance = c_int(1)
    DwfDmmContinuity = c_int(2)
    DwfDmmDiode = c_int(3)
    DwfDmmDCVoltage = c_int(4)
    DwfDmmACVoltage = c_int(5)
    DwfDmmDCCurrent = c_int(6)
    DwfDmmACCurrent = c_int(7)
    DwfDmmDCLowCurrent = c_int(8)
    DwfDmmACLowCurrent = c_int(9)
    DwfDmmTemperature = c_int(10)
    
    AnalogOutNodeCarrier = c_int(0)
    AnalogOutNodeFM = c_int(1)
    AnalogOutNodeAM = c_int(2)
    
    DwfAnalogOutModeVoltage = c_int(0)
    DwfAnalogOutModeCurrent = c_int(1)
    
    DwfAnalogOutIdleDisable = c_int(0)
    DwfAnalogOutIdleOffset = c_int(1)
    DwfAnalogOutIdleInitial = c_int(2)
    DwfAnalogOutIdleHold = c_int(3)
    
    DwfDigitalInClockSourceInternal = c_int(0)
    DwfDigitalInClockSourceExternal = c_int(1)
    DwfDigitalInClockSourceExternal2 = c_int(2)
    
    DwfDigitalInSampleModeSimple = c_int(0)
    # Alternate samples: noise|sample|noise|sample|...
    # Where noise is more than 1 transition between 2 samples
    DwfDigitalInSampleModeNoise = c_int(1)
    
    DwfDigitalOutOutputPushPull = c_int(0)
    DwfDigitalOutOutputOpenDrain = c_int(1)
    DwfDigitalOutOutputOpenSource = c_int(2)
    DwfDigitalOutOutputThreeState = c_int(3) # for custom and random
    
    DwfDigitalOutTypePulse = c_int(0)
    DwfDigitalOutTypeCustom = c_int(1)
    DwfDigitalOutTypeRandom = c_int(2)
    DwfDigitalOutTypeROM = c_int(3)
    DwfDigitalOutTypeState = c_int(4)
    DwfDigitalOutTypePlay = c_int(5)
    
    DwfDigitalOutIdleInit = c_int(0)
    DwfDigitalOutIdleLow = c_int(1)
    DwfDigitalOutIdleHigh = c_int(2)
    DwfDigitalOutIdleZet = c_int(3)
    
    DwfAnalogImpedanceImpedance = c_int(0)           # Ohms
    DwfAnalogImpedanceImpedancePhase = c_int(1)      # Radians
    DwfAnalogImpedanceResistance = c_int(2)          # Ohms
    DwfAnalogImpedanceReactance = c_int(3)           # Ohms
    DwfAnalogImpedanceAdmittance = c_int(4)          # Siemen
    DwfAnalogImpedanceAdmittancePhase = c_int(5)     # Radians
    DwfAnalogImpedanceConductance = c_int(6)         # Siemen
    DwfAnalogImpedanceSusceptance = c_int(7)         # Siemen
    DwfAnalogImpedanceSeriesCapacitance = c_int(8)   # Farad
    DwfAnalogImpedanceParallelCapacitance = c_int(9) # Farad
    DwfAnalogImpedanceSeriesInductance = c_int(10)   # Henry
    DwfAnalogImpedanceParallelInductance = c_int(11) # Henry
    DwfAnalogImpedanceDissipation = c_int(12)        # factor
    DwfAnalogImpedanceQuality = c_int(13)            # factor
    DwfAnalogImpedanceVrms = c_int(14)               # Vrms
    DwfAnalogImpedanceVreal = c_int(15)              # V real
    DwfAnalogImpedanceVimag = c_int(16)              # V imag
    DwfAnalogImpedanceIrms = c_int(17)               # Irms
    DwfAnalogImpedanceIreal = c_int(18)              # I real
    DwfAnalogImpedanceIimag = c_int(19)              # I imag
    
    DwfParamUsbPower = c_int(2)        # 1 keep the USB power enabled even when AUX is connected, Analog Discovery 2
    DwfParamLedBrightness = c_int(3)   # LED brightness 0 ... 100%, Digital Discovery
    DwfParamOnClose = c_int(4)         # 0 continue, 1 stop, 2 shutdown
    DwfParamAudioOut = c_int(5)        # 0 disable / 1 enable audio output, Analog Discovery 1, 2
    DwfParamUsbLimit = c_int(6)        # 0..1000 mA USB power limit, -1 no limit, Analog Discovery 1, 2
    DwfParamAnalogOut = c_int(7)       # 0 disable / 1 enable
    DwfParamFrequency = c_int(8)       # Hz
    DwfParamExtFreq = c_int(9)         # Hz
    DwfParamClockMode = c_int(10)      # 0 internal, 1 output, 2 input, 3 IO
    DwfParamTempLimit = c_int(11)      #
    DwfParamFreqPhase = c_int(12)      #
    DwfParamDigitalVoltage = c_int(13) # mV
    DwfParamFreqPhaseSteps = c_int(14) # readonly
    
    DwfWindowRectangular = c_int(0)
    DwfWindowTriangular = c_int(1)
    DwfWindowHamming = c_int(2)
    DwfWindowHann = c_int(3)
    DwfWindowCosine = c_int(4)
    DwfWindowBlackmanHarris = c_int(5)
    DwfWindowFlatTop = c_int(6)
    DwfWindowKaiser = c_int(7)
    DwfWindowBlackman = c_int(8)
    DwfWindowFlatTopM = c_int(9)
    
    # analog input coupling:
    DwfAnalogCouplingDC = c_int(0)
    DwfAnalogCouplingAC = c_int(1)
    
    # FIR and IIR filters
    DwfFiirWindow = c_int(0)
    DwfFiirFir = c_int(1)
    DwfFiirIirButterworth = c_int(2)
    DwfFiirIirChebyshev = c_int(3)
    
    DwfFiirLowPass = c_int(0)
    DwfFiirHighPass = c_int(1)
    DwfFiirBandPass = c_int(2)
    DwfFiirBandStop = c_int(3)
    
    DwfFiirRaw = c_int(0)
    DwfFiirDecimate = c_int(1)
    DwfFiirAverage = c_int(2)
    
    # OBSOLETE but supported, avoid using the following in new projects:
    DwfParamKeepOnClose = c_int(1)
    # keep the device running after close, use DwfParamOnClose
    
    # use DwfTriggerSlope
    trigcondRisingPositive = c_int(0)
    trigcondFallingNegative = c_int(1)
    
    # use DwfState
    stsRdy = c_ubyte(0)
    stsArm = c_ubyte(1)
    stsDone = c_ubyte(2)
    stsTrig = c_ubyte(3)
    stsCfg = c_ubyte(4)
    stsPrefill = c_ubyte(5)
    stsNotDone = c_ubyte(6)
    stsTrigDly = c_ubyte(7)
    stsError = c_ubyte(8)
    stsBusy = c_ubyte(9)
    stsStop = c_ubyte(10)
    
    # use device ID
    enumfilterEExplorer = c_int(1)
    enumfilterDiscovery = c_int(2)
    enumfilterDiscovery2 = c_int(3)
    enumfilterDDiscovery = c_int(4)

class DwfFnParamOpt:
    """
    @Description
    This entity holds different possible parameters'
    values for FDwf[...] functions, their meaning
    to be more intuitive.
    """
    
    #####################################################
    ### Attributes ready to use by any call to        ###
    ### dwf lib func. These abstract c_[...] classes. ###
    #####################################################
    
    FIRST_DEV = c_int(-1)
    INIT_HND = c_int(0)

class DwfConnectOpt:
    """
    @Description
    There are different modes to connect to a device, simply
    with an index/handler or even with the host ip address.
    This one can be changed to not have the same address.
    """
    
    #####################################################
    ### SOP-Settings Options, They will be used only  ###
    ### with ...OpenEx function.                      ###
    #####################################################
    
    SOP_INDEX = "index:#"
    SOP_SERIALNR = "sn:##########"
    SOP_NAMEDEVN = "name:device-name"
    SOP_CONFIG = "config:#"
    SOP_IP = "ip:#.#.#.#/host"
    SOP_IPUSERPASS = "ip:user:pass@#.#.#.#/host"
    SOP_USERUNAME = "user:username"
    SOP_PASSPW = "pass:password"
    SOP_SECURE = "secure:#"
    SOP_ENUMFIRST = "*"
