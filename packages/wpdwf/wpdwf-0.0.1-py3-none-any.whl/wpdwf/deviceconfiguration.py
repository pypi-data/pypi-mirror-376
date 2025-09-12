
# Custom files
from wfoptionsconstants import DwfSymbolsConstants as wdsc
from enumfuncconstants import DwfFuncCorrelationDevice
from wfoptionsconstants import (DwfSymbolsConstants, DwfFnParamOpt)
from dwfresource import BindingsLinkUp
from dwfexeptions import ErrorWpFnGenericInstrument

# Stdlib file(s)
from ctypes import (CFUNCTYPE, POINTER, c_char,
                    c_int, c_ubyte, create_string_buffer)

class DeviceResources:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationDevice.cFDwfParamSet, # Device Enumeration
            DwfFuncCorrelationDevice.cFDwfParamGet,
            DwfFuncCorrelationDevice.cFDwfEnum,
            DwfFuncCorrelationDevice.cFDwfEnumStart,
            DwfFuncCorrelationDevice.cFDwfEnumStop,
            DwfFuncCorrelationDevice.cFDwfEnumDeviceType,
            DwfFuncCorrelationDevice.cFDwfEnumDeviceIsOpened,
            DwfFuncCorrelationDevice.cFDwfEnumUserName,
            DwfFuncCorrelationDevice.cFDwfEnumDeviceName,
            DwfFuncCorrelationDevice.cFDwfEnumSN,
            DwfFuncCorrelationDevice.cFDwfEnumConfig,
            DwfFuncCorrelationDevice.cFDwfEnumConfigInfo,
            DwfFuncCorrelationDevice.cFDwfDeviceOpen, # Device Control
            DwfFuncCorrelationDevice.cFDwfDeviceOpenEx,
            DwfFuncCorrelationDevice.cFDwfDeviceConfigOpen,
            DwfFuncCorrelationDevice.cFDwfDeviceClose,
            DwfFuncCorrelationDevice.cFDwfDeviceCloseAll,
            DwfFuncCorrelationDevice.cFDwfDeviceAutoConfigureSet,
            DwfFuncCorrelationDevice.cFDwfDeviceAutoConfigureGet,
            DwfFuncCorrelationDevice.cFDwfDeviceReset,
            DwfFuncCorrelationDevice.cFDwfDeviceEnableSet,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerInfo,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerSet,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerGet,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerPC,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerSlopeInfo,
            DwfFuncCorrelationDevice.cFDwfDeviceParamSet,
            DwfFuncCorrelationDevice.cFDwfDeviceParamGet,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerInfo,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerSet,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerGet,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerPC,
            DwfFuncCorrelationDevice.cFDwfDeviceTriggerSlopeInfo
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfParamSet, # Device Enumeration
            BindingsLinkUp.resDwf.FDwfParamGet,
            BindingsLinkUp.resDwf.FDwfEnum,
            BindingsLinkUp.resDwf.FDwfEnumStart,
            BindingsLinkUp.resDwf.FDwfEnumStop,
            BindingsLinkUp.resDwf.FDwfEnumDeviceType,
            BindingsLinkUp.resDwf.FDwfEnumDeviceIsOpened,
            BindingsLinkUp.resDwf.FDwfEnumUserName,
            BindingsLinkUp.resDwf.FDwfEnumDeviceName,
            BindingsLinkUp.resDwf.FDwfEnumSN,
            BindingsLinkUp.resDwf.FDwfEnumConfig,
            BindingsLinkUp.resDwf.FDwfEnumConfigInfo,
            BindingsLinkUp.resDwf.FDwfDeviceOpen, # Device Control
            BindingsLinkUp.resDwf.FDwfDeviceOpenEx,
            BindingsLinkUp.resDwf.FDwfDeviceConfigOpen,
            BindingsLinkUp.resDwf.FDwfDeviceClose,
            BindingsLinkUp.resDwf.FDwfDeviceCloseAll,
            BindingsLinkUp.resDwf.FDwfDeviceAutoConfigureSet,
            BindingsLinkUp.resDwf.FDwfDeviceAutoConfigureGet,
            BindingsLinkUp.resDwf.FDwfDeviceReset,
            BindingsLinkUp.resDwf.FDwfDeviceEnableSet,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerInfo,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerSet,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerGet,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerPC,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerSlopeInfo,
            BindingsLinkUp.resDwf.FDwfDeviceParamSet,
            BindingsLinkUp.resDwf.FDwfDeviceParamGet,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerInfo,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerSet,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerGet,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerPC,
            BindingsLinkUp.resDwf.FDwfDeviceTriggerSlopeInfo
        ]
        self._dtFuncDevRes = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (self.dimlsCfdwf == self.dimlsFdwf and
            len(self._dtFuncDevRes) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncDevRes[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncDevCfg(self) -> dict:
        """ Get reference for self._dtFuncDevRes """
        return self._dtFuncDevRes

class DeviceCfg(BindingsLinkUp):
    """
    @Description
    This class manages one device connected to host
    (i.e ADP2230), in order to control multiple devices,
    simply create other instances of this class. Each device
    has different overall parameters, (i.e ADP2230 has a bigger
    bandwidth at -3dB than AD3), and so on.
    @Notes
    Mapped functions from dwf.h should be more structured,
    then placed in different classes from DwfFuncCorrelationGetters,
    DwfFuncCorrelationSetters, DwfFuncCorrelationEnum and others
    that will appear at some point.
    """
    
    SUBSCHAR = "#"
    
    def __init__(self,
                 indexDev=None,
                 sName="Unknown",
                 bOpen=True,
                 bAuto=True
                 ):
        super().__init__()
        # Attributes :
        # Optional, transmitted if known.
        self._indexDev = indexDev
        self.name = sName.encode("utf-8")
        self.bDevOpen = bOpen
        # Structures that are constant by default should be put
        # in separate files where they can be imported from, an
        # alias works too.
        self.devRes = DeviceResources()
        self.dtFuncDevCfg = self.devRes.dtFuncDevCfg
        # Store locally, but external variables can be used too.
        # WpDwf... will not be used externally.
        self.paramValue = c_int(0)
        self.cDev = c_int(0)
        self.sZOption = create_string_buffer(b"", size=32)
        self._sZSN = create_string_buffer(b"", size=32)
        self.devId = c_int(0)
        self.devRev = c_int(0)
        self.pltfInUse = c_int(0)
        self.sUserName = create_string_buffer(b"", size=32)
        self.sDeviceName = create_string_buffer(b"", size=32)
        self.cConfig = c_int(0)
        self.iVer = c_int(0)
        # C variable, but py should transfer its address.
        self._crHwnd = c_int(0)
        self.AutoConfigure = c_int(0)
        self.trigSrc = c_int(0)
        self.fsSlope = c_int(0)
        self.valueDevParameter = c_int(0)
        # Lib fn-dwf will return 1/True if func has the expected behavior.
        self.tVal = c_int(0)
        try:
            if bAuto is True:
                if self.bDevOpen is True:
                    if self._indexDev is None:
                        # First dev connected
                        self.tVal = self.WpDwfDeviceOpen(
                                         DwfFnParamOpt.FIRST_DEV,
                                         self._crHwnd
                                         )
                        if self.tVal == wdsc.WP_DWFERROR:
                            raise ErrorWpFnGenericInstrument(
                                    "Cannot connect to the first board"
                                    )
                    else:
                        self.tVal = self.WpDwfDeviceOpen(
                                         c_int(self._indexDev),
                                         self._crHwnd
                                         )
                        if self.tVal == wdsc.WP_DWFERROR:
                            raise ErrorWpFnGenericInstrument(
                                    "Cannot connect to the board with index: " +
                                    str(self._indexDev)
                                    )
                elif self.name != b"Unknown":
                    self.sDeviceName.value = self.name
                    # Attach by dev name
                    self.tVal = self.WpDwfDeviceOpenEx(
                                     self.sDeviceName,
                                     self._crHwnd
                                     )
                    if self.tVal == wdsc.WP_DWFERROR:
                        raise ErrorWpFnGenericInstrument(
                                "Cannot connect to the board with direct name: " +
                                self.name
                                )
        except ErrorWpFnGenericInstrument as err:
            if self._lsErrContent.insertErr(err) == wdsc.WP_DWFERROR:
                sys.exit(1)

    @property
    def crHwnd(self) -> int:
        return self._crHwnd.value

    @property
    def indexDev(self) -> int:
        return self._indexDev.value

    @property
    def sZSN(self) -> str:
        return self._sZSN.value

    def WpDwfDeviceOpen(self,
                        idxDevice : c_int,
                        phdwf : POINTER(c_int)
                        ) -> int:
        """
        @Description
        Create local handle for a specific device by its
        index, ...OpenEx can be used to pass a string.
        @Parameters
        idxDevice : device associated number
        phdwf : returned handler
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        Wrap up into a member function
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int))
        def WpFnGeneric(idxDevice, phdwf) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceOpen
                      )(idxDevice, phdwf)
            return iretVal
        return WpFnGeneric(idxDevice, phdwf)

    def WpDwfDeviceConfigOpen(idxDev,
                              idxCfg : c_int,
                              phdwf : POINTER(c_int)
                              ) -> int:
        """
        @Description
        idxCfg can be taken from a call to WpDwfEnumConfig to get in
        pcConfig parameters.
        @Parameters
        idxCfg : one config from DECI... constants
        phdwf : returned handler
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        Configuration based on device capabilities will be
        predefined into a separate file.
        """
        @CFUNCTYPE(c_int, c_int, c_int, POINTER(c_int))
        def WpFnGeneric(idxDev, idxCfg, phdwf) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceConfigOpen
                      )(idxDev, idxCfg, phdwf)
            return iretVal
        return WpFnGeneric(idxDev, idxCfg, phdwf)

    def WpDwfDeviceOpenEx(self,
                          szOpt : POINTER(c_char),
                          phdwf : POINTER(c_int)
                          ) -> int:
        """
        @Description
        Open device through string based entry, for example,
        (*) "name:Analog Discovery 3\nindex:1" in a similar way
        can be done with other Mixed/Signals Digilent devices.
        @Parameters
        szOpt : string value with a predefined value (*)
        phdwf : returned handler
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        szOpt will have predefined strings 
        in this class for every dev.
        """
        @CFUNCTYPE(c_int, POINTER(c_char), POINTER(c_int))
        def WpFnGeneric(szOpt, phdwf) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceOpenEx
                      )(szOpt, phdwf)
            return iretVal
        return WpFnGeneric(szOpt, phdwf)

    def WpDwfDeviceClose(self,
                         hdwf : c_int
                         ) -> int:
        """
        @Description
        Close a certain device, this wrapper hold devices by names <-> indx
        to be more intuitive.
        @Parameters
        hdwf : handler value taken from one of the ...Open functions.
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        Multiple devices can be closed or just one through
        a single call with custom functions in files specific
        classes.
        """
        @CFUNCTYPE(c_int, c_int)
        def WpFnGeneric(hdwf) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceClose
                      )(hdwf)
            return iretVal
        return WpFnGeneric(hdwf)

    def WpDeviceCloseAll(self) -> int:
        """
        @Description
        Remove handlers from all devices.
        @Parameters
        None
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int)
        def WpFnGeneric(hdwf) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceCloseAll
                      )(hdwf)
            return iretVal
        return WpFnGeneric(hdwf)

    def WpDwfDeviceEnableSet(self,
                             hdwf : c_int,
                             fEnable : c_int
                             ) -> int:
        """
        @Description
        en/disable device ~ports~
        @Parameters
        hdwf : device handler
        fEnable : 1 or 0 to enable or disable
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, c_int)
        def WpFnGeneric(hdwf, fEnable) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceEnableSet
                      )(hdwf, fEnable)
            return iretVal
        return WpFnGeneric(hdwf, fEnable)

    def WpDwfDeviceAutoConfigureSet(self,
                                    hdwf : c_int,
                                    fAutoConfigure : c_int
                                    ) -> int:
        """
        @Description
        Let the device firmware be in a known state automatically.
        @Parameters
        hdwf : device handler
        fAutoConfigure : 0:disable, 1:enable, 3:dynamic
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        It is not necessarily to be called, upon opening the device,
        it will be preconfigured.
        """
        @CFUNCTYPE(c_int, c_int, c_int)
        def WpFnGeneric(hdwf, fAutoConfigure) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceAutoConfigureSet
                      )(hdwf, fAutoConfigure)
            return iretVal
        return WpFnGeneric(hdwf, fAutoConfigure)

    def WpDwfDeviceAutoConfigureGet(self,
                                    hdwf : c_int,
                                    pfAutoConfigure : POINTER(c_int)
                                    ) -> int:
        """
        @Description
        Obtain one of the three possible auto configure options,
        0:disable, 1:enable, 3:dynamic.
        @Parameters
        hdwf : device handler
        pfAutoConfigure : find if the device has been automatically
                          configured.
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int))
        def WpFnGeneric(hdwf, pfAutoConfigure) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceAutoConfigureGet
                      )(hdwf, pfAutoConfigure)
            return iretVal
        return WpFnGeneric(hdwf, pfAutoConfigure)

    def WpDwfDeviceReset(self,
                         hdwf : c_int
                         ) -> int:
        """
        @Description
        Reconfigure a certain device by its handler.
        @Parameters
        hdwf : device handler
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int)
        def WpFnGeneric(hdwf) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceReset
                      )(hdwf)
            return iretVal
        return WpFnGeneric(hdwf)

    def WpDwfDeviceParamSet(self,
                            hdwf : c_int,
                            param : c_int,
                            value : c_int
                            ) -> int:
        """
        @Description
        Each board has misc options that can be set.
        @Parameters
        hdwf : device handler
        param : certain parameters can be set, like led from
                board, its intensity through a pwm signal
        value : this one is dependent of param, a list will be
                available in a separate file
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, c_int, c_int)
        def WpFnGeneric(hdwf, param, value) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceParamSet
                      )(hdwf, param, value)
            return iretVal
        return WpFnGeneric(hdwf, param, value)

    def WpDwfDeviceParamGet(self,
                            hdwf : c_int,
                            param : c_int,
                            pvalue : POINTER(c_int)
                            ) -> int:
        """
        @Description
        Each board has misc options that their value can be obtained.
        @Parameters
        hdwf : device handler
        param : parameter to get data from
        pvalue : return value
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        the parameters returned values can be stored
        for each device.
        """
        @CFUNCTYPE(c_int, c_int, c_int, POINTER(c_int))
        def WpFnGeneric(hdwf, param, pvalue) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceParamGet
                      )(hdwf, param, pvalue)
            return iretVal
        return WpFnGeneric(hdwf, param, pvalue)

    def WpDwfDeviceTriggerInfo(self,
                               hdwf : c_int,
                               pfstrigsrc : POINTER(c_int)
                               ) -> int:
        """
        @Description
        Get triggers informations, trigger can be set for analog and
        digital inputs, analog and digital outputs, adc amd di/o, all
        indirectly connected via a signal bus with the external trigger.
        @Parameters
        hdwf : device handler
        pfstringsrc : one of TRIG... sources
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        ~signals~ from python perspective can be added to receive
        data/infos into handler functions associated to each device
        in a vector, for example.
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int))
        def WpFnGeneric(hdwf, pfstrigsrc) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceTriggerInfo
                      )(hdwf, pfstrigsrc)
            return iretVal
        return WpFnGeneric(hdwf, pfstrigsrc)

    def WpDwfDeviceTriggerSet(self,
                              hdwf : c_int,
                              idxPin : c_int,
                              trigsrc : c_ubyte
                              ) -> int:
        """
        @Description
        Configures only trigger I/O pin.
        @Parameters
        hdwf : device handler
        idxPin : i/o or ext trig
        trigsrc : one of TRI... sources constant
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        Predefine different trigger setups into constants.
        """
        @CFUNCTYPE(c_int, c_int, c_int, c_ubyte)
        def WpFnGeneric(hdwf, idxPin, trigSrc) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceTriggerSet
                      )(hdwf, idxPin, trigsrc)
            return iretVal
        return WpFnGeneric(hdwf, idxPin, trigSrc)

    def WpDwfDeviceTriggerGet(self,
                              hdwf : c_int,
                              idxPin : c_int,
                              ptrigsrc : POINTER(c_ubyte)
                              ) -> int:
        """
        @Description
        Get configuration for trigger I/O pin.
        @Parameters
        hdwf : device handler
        idxPin : i/o or ext trig
        ptrigsrc : return TRIG... source used previously
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, c_int, POINTER(c_ubyte))
        def WpFnGeneric(hdwf, idxPin, ptrigsrc) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceTriggerGet
                      )(hdwf, idxPin, ptrigsrc)
            return iretVal
        return WpFnGeneric(hdwf, idxPin, ptrigsrc)

    def WpDwfDeviceTriggerPC(self,
                             hdwf : c_int
                             ) -> int:
        """
        @Description
        Arm all triggers connected to the bus.
        @Parameters
        hdwf : device handler
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int)
        def WpFnGeneric(hdwf) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceTriggerPC
                      )(hdwf)
            return iretVal
        return WpFnGeneric(hdwf)

    def WpDwfDeviceTriggerSlopeInfo(self,
                                    hdwf : c_int,
                                    pfsslope : POINTER(c_int)
                                    ) -> int:
        """
        @Description
        Return possible slope settings
        @Parameters
        hdwf : device handler
        pfsslope : TODO: find possible codes
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int))
        def WpFnGeneric(hdwf, pfsslope) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfDeviceTriggerSlopeInfo
                      )(hdwf, pfsslope)
            return iretVal
        return WpFnGeneric(hdwf, pfsslope)

    def __repr__(self):
        """
        @Description
        Get a detailed description of the device in use,
        name, idx, handler associated to it. This is independent
        of device, maybe two devices are used simultaneously (this
        features is not supported natively in waveforms so far ...),
        and its features (to be added) the user could want to be displayed
        somewhere (i.e. terminal, UI, file).
        @Notes
        None
        """
        lcStr = "Bindings Info: {0}" \
                "\nDevice: {1} "     \
                "with ID: {2} "      \
                "and Handler: {3}"
        return lcStr.format(super().__repr__(),
                            self.name.decode("utf-8"),
                            str(self._indexDev),
                            str(self._crHwnd.value)
                            )

class Devices(BindingsLinkUp):
    """
    @Description
    In cases where multiple devices need to be used
    simultaneously, this class comes in handy to manipulate
    them. For gui examples/setups there is no need of threads,
    but if some setup does many operations automatically, then
    maybe it is needed to allocate one or two threads (not one
    for each device), it is easier to multiplex between them.
    @Notes
    EE ~ Electronics Explorer
    AD ~ Analog Discovery
    ADP ~ Analog Discovery Pro
    """
    
    SUCCESS = 0
    FAILURE = -1
    # Attach with name + an index
    EE = f"name:Electronics Explorer\nindex:{DeviceCfg.SUBSCHAR}"
    AD = f"name:Analog Discovery\nindex:{DeviceCfg.SUBSCHAR}"
    AD2 = f"name:Analog Discovery 2\nindex:{DeviceCfg.SUBSCHAR}"
    DD = f"name:Digital Discovery\nindex:{DeviceCfg.SUBSCHAR}"
    ADP3000S = f"name:Analog Discovery Pro 3000 Series\nindex:{DeviceCfg.SUBSCHAR}"
    ADP3450 = f"name:Analog Discovery Pro 3450\nindex:{DeviceCfg.SUBSCHAR}"
    ADP5250 = f"name:Analog Discovery Pro 5250\nindex:{DeviceCfg.SUBSCHAR}"
    EZ7ZMODS = f"name:Eclypse Z7 Zmods\nindex:{DeviceCfg.SUBSCHAR}"
    DPS3340 = f"name:Discovery Power Supply 3340\nindex:{DeviceCfg.SUBSCHAR}"
    AD3 = f"name:Analog Discovery 3\nindex:{DeviceCfg.SUBSCHAR}"
    # TODO: Other possible ways ...
    DEV = 0
    DEVIDX = 1
    DEVNAME = 2
    DEVCONFIG = 3
    
    def __init__(self, lsDevsToUse=[]):
        super().__init__()
        # Attributes :
        self.lsDevsToUse = lsDevsToUse
        self.nrDevs = len(self.lsDevsToUse)
        self.lsDevType = [
            [wdsc.devidEExplorer, 0], [wdsc.devidDiscovery, 0],
            [wdsc.devidDiscovery2, 0], [wdsc.devidDDiscovery, 0],
            [wdsc.devidADP3X50, 0], [wdsc.devidEclypse, 0],
            [wdsc.devidADP5250, 0], [wdsc.devidDPS3340, 0],
            [wdsc.devidDiscovery3, 0], [wdsc.devidADP5470, 0],
            [wdsc.devidADP5490, 0], [wdsc.devidADP2230, 0]
            # To be added
        ]
        self.lsOptEn = [
            wdsc.enumfilterAll, wdsc.enumfilterType,
            wdsc.enumfilterUSB, wdsc.enumfilterNetwork,
            wdsc.enumfilterAXI, wdsc.enumfilterRemote,
            wdsc.enumfilterAudio, wdsc.enumfilterDemo
            # To be added
        ]
        self.lsIdxDevs = []
        # Structures that are constant by default should be put
        # in separate files where they can be imported from, an
        # alias works too.
        self.devRes = DeviceResources()
        self.dtFuncDevCfg = self.devRes.dtFuncDevCfg
        self.lsDvFound = []
        # 0 -> config, 1 -> idxDev, 2 -> size or count
        self.lsConfigsDev = [
            [wdsc.DECIAnalogInChannelCount, 0, 0],
            [wdsc.DECIAnalogOutChannelCount, 0, 0],
            [wdsc.DECIAnalogIOChannelCount, 0, 0],
            [wdsc.DECIDigitalInChannelCount, 0, 0],
            [wdsc.DECIDigitalOutChannelCount, 0, 0],
            [wdsc.DECIDigitalIOChannelCount, 0, 0],
            [wdsc.DECIAnalogInBufferSize, 0, 0],
            [wdsc.DECIAnalogOutBufferSize, 0, 0],
            [wdsc.DECIDigitalInBufferSize, 0, 0],
            [wdsc.DECIDigitalOutBufferSize, 0, 0],
            [wdsc.DECIPowerOutChannelCount, 0, 0],
            [wdsc.DECIPowerOutBufferSize, 0, 0],
            [wdsc.DECIAnalogOutPlaySize, 0, 0]
        ]
        self.cdIdx, self.cdSzCnt = 1, 2
        # One or more devs
        self.nrDevs = c_int(0)
        self.lsNameSN = []

    def WpDwfParamSet(self,
                      param : c_int,
                      value : c_int
                      ) -> int:
        """
        @Description
        Parameter is set only locally, after connecting
        to a device these will be applied. Checkout
        DwfParam... constants from DwfSymbolsConstants.
        @Parameters
        param : Predefined constant for features like
                modyfing IO voltages of some boards.
        value : [3...13] range
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        These parameters can be set to certain
        boards only, check WaveForms SDK manual, but
        this wrapper should have all enclosed into
        functions.
        """
        @CFUNCTYPE(c_int, c_int, c_int)
        def WpFnGeneric(param, value) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfParamSet
                      )(param, value)
            return iretVal
        return WpFnGeneric(param, value)

    def WpDwfParamGet(self,
                      param : c_int,
                      pvalue : POINTER(c_int)
                      ) -> int:
        """
        @Description
        Retrive parameter value that was set with
        WpDwfParamSet. These attributes are set
        locally within dwf.dll scope.
        @Parameters
        param : Predefined constant (@see DwfSymbolsConstants)
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int))
        def WpFnGeneric(param, pvalue) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfParamGet
                      )(param, pvalue)
            return iretVal
        return WpFnGeneric(param, pvalue)

    def WpDwfEnum(self,
                  enumfilter : c_int,
                  pnDevice : POINTER(c_int)
                  ) -> int:
        """
        @Description
        WpDwfEnum should be called first, but this will
        be handled by wrapper, there is no need for the
        end user to call this function explicitly.
        @Parameters
        enumfilter : filter value, checkout WFOptionsConstants
        pnDevice : nr of devices from enumfilter set
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int))
        def WpFnGeneric(enumfilter, pnDevice) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnum
                      )(enumfilter, pnDevice)
            return iretVal
        return WpFnGeneric(enumfilter, pnDevice)

    def WpDwfEnumStart(self,
                       enumfilter : c_int
                       ) -> int:
        """
        @Description
        Count devices connected to the host, specific to
        a certain type `enumfilter`. This function can be
        used with WpDwfEnumStop.
        @Parameters
        enumfilter : filter value, checkout WFOptionsConstants
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int)
        def WpFnGeneric(enumfilter) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumStart
                      )(enumfilter)
            return iretVal
        return WpFnGeneric(enumfilter)

    def WpDwfEnumStop(self,
                      pnDevice : POINTER(c_int)
                      ) -> int:
        """
        @Description
        Get in pnDevice reference the number of devices
        attachted to host. This function can be
        used with WpDwfEnumStart.
        @Parameters
        pnDevice : nr of devices from enumfilter set
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, POINTER(c_int))
        def WpFnGeneric(pnDevice) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumStop
                      )(pnDevice)
            return iretVal
        return WpFnGeneric(pnDevice)

    def WpDwfEnumDeviceType(self,
                            idxDevice : c_int,
                            pDeviceId : POINTER(c_int),
                            pDeviceRevision : POINTER(c_int)
                            ) -> int:
        """
        @Description
        Classify a certain device selected through an index
        that can be found from the above Enum functions.
        @Parameters
        idxDevice : index for a device
        pDeviceId : device id - board type
        pDeviceRevision : rev[A.x/B.x/C.x/...]
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int),
                   POINTER(c_int))
        def WpFnGeneric(idxDevice, pDeviceId, pDeviceRevision) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumDeviceType
                      )(idxDevice, pDeviceId, pDeviceRevision)
            return iretVal
        return WpFnGeneric(idxDevice, pDeviceId, pDeviceRevision)

    def WpDwfEnumDeviceIsOpened(self,
                                idxDevice : c_int,
                                pfIsUsed : POINTER(c_int)
                                ) -> int:
        """
        @Description
        Check if one device with a specific index is being
        used by a process on the host PC.
        @Parameters
        idxDevice : index for a device
        pfIsUsed : reference that stores 0x1 or 0x0 on 32 bit
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        Nr of devices can be found with the above Enum
        functions, this is abstracted with this wrapper.
        Upon an object instantiation, all devices connected
        will be stored in a list accessible to many other
        resources.
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int))
        def WpFnGeneric(idxDevice, pfIsUsed) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumDeviceIsOpened
                      )(idxDevice, pfIsUsed)
            return iretVal
        return WpFnGeneric(idxDevice, pfIsUsed)

    def WpDwfEnumUserName(self,
                          idxDevice : c_int,
                          szUserName : POINTER(c_char)
                          ) -> int:
        """
        @Description
        Get the user name of a certain device with
        its index.
        @Parameters
        idxDevice : index for a device
        szUserName : string with the name of user
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_char))
        def WpFnGeneric(idxDevice, szUserName) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumUserName
                      )(idxDevice, szUserName)
            return iretVal
        return WpFnGeneric(idxDevice, szUserName)

    def WpDwfEnumDeviceName(self,
                            idxDevice : c_int,
                            szDeviceName : POINTER(c_char)
                            ) -> int:
        """
        @Description
        Get the device name of a certain board with
        its index.
        @Parameters
        idxDevice : index for a device
        szDeviceName : string with the name of device
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_char))
        def WpFnGeneric(idxDevice, szDeviceName) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumDeviceName
                      )(idxDevice, szDeviceName)
            return iretVal
        return WpFnGeneric(idxDevice, szDeviceName)

    def WpDwfEnumSN(self,
                    idxDevice : c_int,
                    szSN : POINTER(c_char)
                    ) -> int:
        """
        @Description
        Get the serial number of a certain board with
        its index.
        @Parameters
        idxDevice : index for a device
        szSN : string with serial number
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_char))
        def WpFnGeneric(idxDevice, szSN) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumSN
                      )(idxDevice, szSN)
            return iretVal
        return WpFnGeneric(idxDevice, szSN)

    def WpDwfEnumConfig(self,
                        idxDevice : c_int,
                        pcConfig : POINTER(c_int)
                        ) -> int:
        """
        @Description
        Get number of configs for a specific device
        with its index.
        @Parameters
        idxDevice : index for a device
        pcConfig : reference to nr of configs
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        None
        """
        @CFUNCTYPE(c_int, c_int, POINTER(c_int))
        def WpFnGeneric(idxDevice, pcConfig) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumConfig
                      )(idxDevice, pcConfig)
            return iretVal
        return WpFnGeneric(idxDevice, pcConfig)

    def WpDwfEnumConfigInfo(self,
                            idxConfig : c_int,
                            info : c_int,
                            pValue : POINTER(c_int)
                            ) -> int:
        """
        @Description
        Get nr of features for a certain config.
        @Parameters
        idxConfig : value found using the above func ~ max: pcConfig.value
        info : class of configs ~ checkout DECI... from WFOptionsConstants
        pValue : returned value for certain configuratin
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        Enum functions should be used before opening a device,
        functions' order line specify this.
        """
        @CFUNCTYPE(c_int, c_int, c_int,
                   POINTER(c_int))
        def WpFnGeneric(idxConfig, info, pValue) -> int:
            iretVal = self.dtFuncDevCfg.get(
                        DwfFuncCorrelationDevice.cFDwfEnumConfigInfo
                      )(idxConfig, info, pValue)
            return iretVal
        return WpFnGeneric(idxConfig, info, pValue)

    def findDev(self,
                enumOpt : c_int | None = wdsc.enumfilterAll,
                bAutoNoBlock=False
                ) -> int:
        """
        @Description
        Detect what devices are connected to the host via Enum
        functions, store all types of devices. Having them stored
        locally it will be easier later to attach to them.
        @Parameters
        enumOpt : enumeration type, by default it checks for all devs
        bAutoNoBlock : default it is False to get number of devs
        @Return
        0/-1, 0 on Success, -1 on Failure
        """
        # If auto is selected when creating an obj,
        # it will not be necessary calling this function
        ENUM_FNCCK = 0x03
        MASK = 0xFF
        SHIFT_POS = 1
        idxStart = 0
        if bAutoNoBlock is False:
            if enumOpt is None:
                for idx in range(idxStart, len(self.lsOptEn)):
                    iretVal = self.WpDwfEnum(
                                   self.lsOptEn[idx],
                                   self.nrDevs
                                   )
                    if iretVal != wdsc.WP_DWFERROR:
                        # Back up a tuple - [0] -> enumfilter;
                        # [1] -> how many devs
                        self.lsIdxDevs.append(
                             tuple([self.lsOptEn[idx], self.nrDevs.value])
                             )
            else:
                iretVal = self.WpDwfEnum(
                               enumOpt,
                               self.nrDevs
                               )
        else:
            if enumOpt is None:
                for idx in range(idxStart, len(self.lsOptEn)):
                    iretVal = self.WpDwfEnumStart(
                                   self.lsOptEn[idx]
                                   )
                    flgFnSt = flgFnSt | iretVal
                    flgEnSt = flgEnSt << SHIFT_POS
                    iretVal = self.WpDwfEnumStop(
                                   self.nrDevs
                                   )
                    flgEnSt = flgEnSt | iretVal
                    if flgEnSt & MASK == ENUM_FNCCK:
                        # Back up a tuple:[0] -> enumfilter [1] -> no. devs
                        self.lsIdxDevs.append(
                             tuple([lsOptEn[idx], self.nrDevs.value])
                             )
        return Devices.SUCCESS

    def findDevByIdx(self,
                     idxDev : int | None = -1,
                     bSingleDev=False
                     ) -> int:
        """
        @Description
        Sweep over devices with a known index or go for any
        connected. This approach is similar to enumation filters,
        where enumfilterAll is used.
        @Parameters
        idxDev : check for any device if default value of -1 is used
        bSingleDev : sweep over any existent dev, otherwise use a
                     certain one with a known index
        @Return
        0/-1, 0 on Success, -1 on Failure
        """
        # | (): # list of tuples or a single tuple
        flgFnSt = 0
        ENUM_FNCCK = 0x03
        MASK = 0xFF
        SHIFT_POS = 1
        idxStart = 0
        devId, devRev = c_int(0), c_int(0)
        devOpened = c_int(0)
        pLeft, pRight = 0, 1
        if bSingleDev is False and len(self.lsIdxDevs) != 0:
            # Somewhere in the class hook up a list
            # to keep track of all devs that are ON
            for idx in range(idxStart, len(self.lsDevType)):
                iretVal = self.WpDwfEnumDeviceIsOpened(
                               c_int(self.lsIdxDevs[idx]),
                               devOpened
                               )
                flgFnSt = flgFnSt | iretVal
                flgEnSt = flgEnSt << SHIFT_POS
                # idxDevs ? after a call to findDev ...
                iretVal = self.WpDwfEnumDeviceType(
                               c_int(self.lsIdxDevs[idx]),
                               devId,
                               devRev
                               )
                flgEnSt = flgEnSt | iretVal
                if flgEnSt & MASK == ENUM_FNCCK:
                    # [0] -> idx; [1] -> Id; [2] -> rev; [3] -> state
                    self.lsDvFound.append(
                         tuple([self.lsIdxDevs[idx][pLeft], devId.value,
                               devRev.value, devOpened.value]
                               )
                         )
                    self.lsIdxDevs[idx][pRight] += 1
                flgFnSt = 0
        else:
            if idxDev != -1:
                iretVal = self.WpDwfEnumDeviceIsOpened(
                               c_int(idxDev),
                               devOpened
                               )
                flgEnSt = flgEnSt | iretVal
                flgEnSt = flgEnSt << SHIFT_POS
                iretVal = self.WpDwfEnumDeviceType(
                               c_int(idxDev),
                               devId,
                               devRev
                               )
                flgEnSt = flgEnSt | iretVal
                if flgEnSt & MASK == ENUM_FNCCK:
                    # Idea: use yield to group them into a generator
                    self.lsDvFound.append(
                         tuple([idxDev, devId.value,
                               devRev.value, devOpened.value]
                               )
                         )
        return Devices.SUCCESS

    def findDevByName(self,
                      idxDev : int | None = -1,
                      sName : str = "Unknown"
                      ) -> int:
        """
        @Description
        Detect all devices with a certain name, like Electronic Explorer,
        all of them, or just one if the index is known.
        @Parameters
        idxDev : value starting from 0 associated to a device
        sName : device name such as, Analog Discovery, checkout
                static variables of this class
        @Return
        0/-1, 0 on Success, -1 on Failure
        """
        ENUM_FNCCK = 0x07
        MASK = 0xFF
        SHIFT_POS = 1
        sZSN = create_string_buffer(b"", size=32)
        sDeviceName = create_string_buffer(b"", size=32)
        sUserName = create_string_buffer(b"", size=32)
        if sName == "Unknown" and idxDev == -1:
            iStop = True
            while iStop:
                iretVal = self.WpDwfEnumDeviceName(idxDev, sDeviceName)
                iretVal = iretVal << SHIFT_POS
                iretVal = self.WpDwfEnumSN(idxDev, sZSN)
                iretVal = iretVal << SHIFT_POS
                iretVal = self.WpDwfEnumUserName(idxDev, sUserName)
                if iretVal & MASK == ENUM_FNCCK:
                    self.lsNameSN.append(
                         tuple([sDeviceName.value, sZSN.value, sUserName.value])
                         )
                else:
                    iStop = False
            return Devices.SUCCESS
        else:
            iretVal = self.WpDwfEnumDeviceName(idxDev, sDeviceName)
            iretVal = iretVal << SHIFT_POS
            iretVal = self.WpDwfEnumSN(idxDev, sZSN)
            iretVal = iretVal << SHIFT_POS
            iretVal = self.WpDwfEnumUserName(idxDev, sUserName)
            if iretVal & MASK == ENUM_FNCCK:
                self.lsNameSN.append(
                     tuple([sDeviceName.value, sZSN.value, sUserName.value])
                     )
                return Devices.SUCCESS
            else:
                return Devices.FAILURE

    def findDevByConfig(self,
                        idxDev : int | None = -1,
                        config : c_int = c_int(0)
                        ) -> tuple | int:
        """
        @Description
        Sweep over connected devices to host w.r to their
        configuration, this criteria identifies the capabilities
        of each device and store them locally in a Devices instance.
        Typically, just one instance to this class is needed.
        @Parameters
        idxDev : value starting from 0 associated to a device
        config : capabilities of device, checkout DECI... constants
                 from wpoptionsconstants
        @Return
        tuple - (index, no. of configs) or just an empty tuple
        """
        idxStart = 0
        lcConfig = config
        nrConfigs = c_int(0)
        if config is not None:
            for idx in range(idxStart, len(self.lsConfigsDev)):
                iretVal = self.WpDwfEnumConfigInfo(
                               c_int(idxDev),
                               lcConfig,
                               nrConfigs
                               )
                if iretVal:
                    self.lsConfigsDev[idx][self.cdIdx] = idxDev
                    self.lsConfigsDev[idx][self.cdSzCnt] = nrConfigs.value
            return Devices.SUCCESS
        else:
            iretVal = self.WpDwfEnumConfig(c_int(idxDev), nrConfigs)
            if iretVal:
                # Device index, number of configs from runtime
                return tuple([idxDev, nrConfigs.value])

    def sweepDevs(self,
                  bCollectAll : bool = True,
                  iSel : int = 0
                  ) -> tuple:
        """
        @Description
        Gather all devices by different categories, to
        have them stored locally, this comes in handy
        when working with multiple boards/devices is
        needed for complex setups. Custom ones will benefit
        from this approach.
        @Parameters
        bCollectAll : Populate or not local vectors with
                      devices connected to host
        iSel : select one of collect/find method
        @Return
        0/-1, 0 on Success, -1 on Failure
        """
        if bCollectAll and iSel is None:
            retFD = self.findDev()
            retFDBI = self.findDevByIdx()
            retFDBN = self.findDevByName()
            retFDBC = self.findDevByConfig()
            return tuple([retFD, retFDBI, retFDBN, retFDBC])
        else:
            match (iSel):
                case (Devices.DEV):
                    retFD = self.findDev()
                    return tuple(retFD)
                case (Devices.DEVIDX):
                    retFDBI = self.findDevByIdx()
                    return tuple(retFDBI)
                case (Devices.DEVNAME):
                    retFDBN = self.findDevByName()
                    return tuple(retFDBN)
                case (Devices.DEVCONFIG):
                    retFDBC = self.findDevByConfig()
                    return tuple(retFDBC)

    def paramDev(self,
                 tIDXN : tuple,
                 param : int,
                 value : int,
                 bGet : bool = False
                 ) -> tuple | int:
        """
        @Description
        It is not quite clear when to call this function,
        after connection of one device or before, it depends
        on how this param <-> value association is stored locally
        in the runtime.
        @Parameters
        tIDXN : tuple with index and name
        param : parameter dependent of the board (Green LED <--|)
        value : val for parameter (duty cycle for pwm signal --|)
        bGet : get or not the param of a device
        @Return
        tuple - (tuple(index, devicename), param, value) extracted,
        so bGet should be set, otherwise an empty tuple
        """
        icParam = c_int(param)
        icValue = c_int(value)
        if not bGet:
            iretVal = self.WpDwfParamSet(icParam, icValue)
            if iretVal:
                return Devices.SUCCESS
        else:
            iretVal = self.WpDwfParamGet(icParam, icValue)
            if iretVal:
                return tuple(tIDXN, icParam, icValue)
