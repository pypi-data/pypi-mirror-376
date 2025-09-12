
# Custom files
from wfoptionsconstants import DwfSymbolsConstants as wdsc
from digitalinstruments import DigitalInstruments
from analoginstruments import AnalogInstruments
from dwfresource import BindingsLinkUp
from enumfuncconstants import DwfFuncCorrelationMisc
from dwfexeptions import ErrorWpFnGenericInstrument

# Stdlib file(s)
from ctypes import (CFUNCTYPE, POINTER, c_char,
                    c_int, c_ubyte, create_string_buffer,
                    c_uint, c_double, c_ulonglong,
                    c_void_p, c_ushort)

class Miscellaneous:
    """
    @Description
    @Notes
    """
    def __init__(self):
        # Seen as ~keys~
        self.lsCfdwf = [
            DwfFuncCorrelationMisc.cFDwfSpectrumWindow,
            DwfFuncCorrelationMisc.cFDwfSpectrumFFT,
            DwfFuncCorrelationMisc.cFDwfSpectrumTransform,
            DwfFuncCorrelationMisc.cFDwfSpectrumGoertzel
        ]
        # Seen as ~values~
        self.lsFdwf = [
            BindingsLinkUp.resDwf.FDwfSpectrumWindow,
            BindingsLinkUp.resDwf.FDwfSpectrumFFT,
            BindingsLinkUp.resDwf.FDwfSpectrumTransform,
            BindingsLinkUp.resDwf.FDwfSpectrumGoertzel
        ]
        self._dtFuncMisc = {}
        # Aux attributes
        self.dimlsCfdwf = len(self.lsCfdwf)
        self.dimlsFdwf = len(self.lsFdwf)
        if (dimlsCfdwf == dimlsFdwf and
            len(self._dtFuncMisc) == 0
            ):
            dSize = self.dimlsCfdwf
            for idx in range(0, dSize):
                self._dtFuncMisc[
                    self.lsCfdwf[idx]
                ] = self.lsFdwf[idx]

    @property
    def dtFuncMisc(self) -> dict:
        """ Get reference for self._dtFuncMisc """
        return self._dtFuncMisc

class MiscellaneousConfig:
    """
    @Description
    This class implements access to all instruments
    similar to pattern generator, logic analyzer.
    @Notes
    None
    """
    def __init__(self, iHnd=None):
        self.misc = Miscellaneous()
        self.dtFuncMisc = self.misc.dtFuncMisc
        # Aux attributes
        # ...

    def WpDwfSpectrumWindow(self,
                            rgdWin : POINTER(c_double),
                            cdWin : c_int,
                            iWindow : c_int,
                            vBeta : c_double, # const
                            vNEBW : POINTER(c_double)
                            ) -> int:
        """
        @Description
        @Parameters
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        """
        @CFUNCTYPE(c_int, POINTER(c_double), c_int,
                   c_int, c_double, POINTER(c_double))
        def WpFnGeneric(rgdWin, cdWin, iWindow, vBeta, vNEBW) -> int:
            iretVal = self.dtFuncMisc.get(
                        DwfFuncCorrelationMisc.cFDwfSpectrumWindow
                      )(cdWin, iWindow, vBeta,
                        vNEBW)
            return iretVal
        return WpFnGeneric(cdWin, iWindow, vBeta,
                           vNEBW)

    def WpDwfSpectrumFFT(self,
                         rgdData : POINTER(c_double), # const
                         cdData : c_int,
                         rgdBin : POINTER(c_double),
                         rgdPhase : POINTER(c_double),
                         cdBin : c_int
                         ) -> int:
        """
        @Description
        @Parameters
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        """
        @CFUNCTYPE(c_int, POINTER(c_double), c_int,
                   POINTER(c_double), POINTER(c_double), c_int)
        def WpFnGeneric(rgdData, cdData, rgdBin, rgdPhase, cdBin) -> int:
            iretVal = self.dtFuncMisc.get(
                        DwfFuncCorrelationMisc.cFDwfSpectrumFFT
                      )(rgdData, cdData, rgdBin, rgdPhase, cdBin)
            return iretVal
        return WpFnGeneric(rgdData, cdData, rgdBin, rgdPhase, cdBin)

    def WpDwfSpectrumTransform(self,
                               rgdData : POINTER(c_double), # const
                               cdData : c_int,
                               rgdBin : POINTER(c_double),
                               rgdPhase : POINTER(c_double),
                               cdBin : c_int,
                               iFirst : c_double,
                               iLast : c_double
                               ) -> int:
        """
        @Description
        @Parameters
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        """
        @CFUNCTYPE(c_int, POINTER(c_double), c_int,
                   POINTER(c_double), POINTER(c_double), c_int,
                   c_double, c_double)
        def WpFnGeneric(rgdData, cdData, rgdBin,
                        rgdPhase, cdBin, iFirst,
                        iLast) -> int:
            iretVal = self.dtFuncMisc.get(
                        DwfFuncCorrelationMisc.cFDwfSpectrumTransform
                      )(rgdData, cdData, rgdBin,
                        rgdPhase, cdBin, iFirst,
                        iLast)
            return iretVal
        return WpFnGeneric(rgdData, cdData, rgdBin,
                           rgdPhase, cdBin, iFirst,
                           iLast)

    def WpDwfSpectrumGoertzel(self,
                              rgdData : POINTER(c_double), # const
                              cdData : c_int,
                              pos : c_double,
                              pMag : POINTER(c_double),
                              pRad : POINTER(c_double)
                              ) -> int:
        """
        @Description
        @Parameters
        @Return
        0 or 1, False or True, True/1 is returned in case
        of correct behavior.
        @Notes
        """
        @CFUNCTYPE(c_int, POINTER(c_double), c_int,
                   c_double, POINTER(c_double), POINTER(c_double))
        def WpFnGeneric(rgdData, cdData, pos,
                        pMag, pRad) -> int:
            iretVal = self.dtFuncMisc.get(
                        DwfFuncCorrelationMisc.cFDwfSpectrumGoertzel
                      )(rgdData, cdData, pos,
                        pMag, pRad)
            return iretVal
        return WpFnGeneric(rgdData, cdData, pos,
                           pMag, pRad)

class WaveFormsCommonInstrumentation:
    """
    @Description
    This class holds the entire background of
    instruments access to low-level hardware. Local objects
    for digital/analog instruments are abstracted here, w.r to
    what board is connected to local machine.
    @Notes
    None
    """
    def __init__(self, lsDevsToUse=[], dctDevsOptConf={}):
        # Configuration parameters come in here
        self.lsDevsToUse = lsDevsToUse
        self.nrDevs = len(self.lsDevsToUse)
        self.lsDI_itemDev = []
        for x in range(0, self.nrDevs):
            self.lsDI_itemDev.append(
                DigitalInstruments(self.lsDevsToUse[x].crHwnd)
                )
        # Similar approach to be done for below instruments.
        #self.AI_itemDev = AnalogInstruments()
        #self.MISC_itemDev = MiscellaneousConfig()

    def confDI(self,
               nrDev : int,
               dInstFlags={"IO":False,"DigitalProtocols":False
                           },
               dFlags={"Io":False,"Uart":False,
                       "Spi":False,"I2c":False,"Can":False,
                       "Swd":False
                       },
               data={"Io":{"bReset":False,"bStatus":False,
                           "bEnable":False,"bInfo":False,
                           "format":32,
                           "dDio":{"DIO0":0,"DIO1":0,"DIO2":0,"DIO3":0,
                                   "DIO4":0,"DIO5":0,"DIO6":0,"DIO7":0,
                                   "DIO8":0,"DIO9":0,"DIO10":0,"DIO11":0,
                                   "DIO12":0,"DIO13":0,"DIO14":0,"DIO15":0},
                           "dOutput":{"Mask":0,"DIO":-1,"iDIO":-1},
                           "dPull":{"PullUp":0,"PullDown":0,
                                    "iPullUp":0,"iPullDown":0,
                                    "MaskPullUp":0,"MaskPullDown":0},
                           "dDrive":{"Channel":0,"Amplitude":0.0,"Slew":0,
                                     "iAmplitude":0.0,"iSlew":0,"AmpMin":0.0,
                                     "AmpMax":0.0,"AmpSteps":0,"SlewSteps":0},
                           "dInput":{"stsMask":0,"Mask":0}},
                     "Uart":{"bReset":False,"frequency":0.0,
                             "bRead":False,"bWrite":False,
                             "chDIOTx":None,"chDIORx":None,
                             "nrCntTx":1,
                             "data":{"Polarity":0,"Parity":0,"BufferTx":[],
                                     "BufferRx":[],"CntRx":0}},
                     "Spi":{"bReset":False,"frequency":0.0,
                            "chDIOClock":None,"chDIOData":None,
                            "chDIOCS":None,"csIdle":0,
                            "dataMode":0,"format":8,
                            "bRead":False,"nrCnt":1,
                            "bWrite":False,"idle":None,
                            "data":{"Cmd":0,"BufferTx":[],"BufferRx":[],
                                    "Mode":0,"Delay":0.0,"MSBFirst":1}},
                     "I2c":{"bReset":False,"frequency":0.0,
                            "bNak":False,"bClear":False,
                            "bStretch":False,"bRead":False,
                            "bWrite":False,"bSpy":False,
                            "nrCnt":1,"chDIOScl":None,
                            "chDIOSda":None,"timeout":0.0,
                            "data":{"Nak":0,"Clear":0,"BufferRx":[],
                                    "BufferTx":[],"Addr":0,"BufferSpy":[],
                                    "SpyCntData":0,"SpyStartStop":(0,0)}},
                     "Can":{"bReset":False,"frequency":0.0,
                            "bRead":False,"bWrite":False,
                            "chDIOTx":None,"chDIORx":None,
                            "nrCntRx":1,
                            "data":{"Polarity":0,"ID":0,"BufferTx":[],
                                    "BufferRx":[],"DLC":0,"Extended":0,
                                    "Remote":0,"Status":0}},
                     "Swd":{"bReset":False,"frequency":0.0,
                            "chDIOCk":None,"chDIOIo":None,
                            "bPark":False,"bNak":False,
                            "bIdle":False,"bClear":False,
                            "bRead":False,"bWrite":False,
                            "data":{"Turn":0,"Trail":0,"Drive":0,
                                    "Continue":0,"High":0,"CmdTx":0,
                                    "CmdRx":0,"Ack":0,"Crc":0,
                                    "Reset":0,"APnDP":0,"A32":0}}
                     }
               ):
        """
        @Description
        @Param
        @Return
        None
        @Notes
        """
        try:
            lsKeys = list(dInstFlags.keys())
            if "IO" in lsKeys:
                if dInstFlags["IO"] and dFlags["Io"]:
                        self.lsDI_itemDev[nrDev].io.Io(
                             data["Io"]["bReset"],
                             data["Io"]["bStatus"],
                             data["Io"]["bEnable"],
                             data["Io"]["bInfo"],
                             data["Io"]["format"],
                             data["Io"]["dDio"],
                             data["Io"]["dOutput"],
                             data["Io"]["dPull"],
                             data["Io"]["dDrive"],
                             data["Io"]["dInput"]
                             )
                        return
            if "DigitalProtocols" in lsKeys:
                if dInstFlags["DigitalProtocols"]:
                    if dFlags["Uart"]:
                        self.lsDI_itemDev[nrDev].dpc.Uart(
                             data["Uart"]["bReset"],
                             data["Uart"]["frequency"],
                             data["Uart"]["bRead"],
                             data["Uart"]["bWrite"],
                             data["Uart"]["chDIOTx"],
                             data["Uart"]["chDIORx"],
                             data["Uart"]["nrCntTx"],
                             data["Uart"]["data"]
                             )
                        return
                    if dFlags["Spi"]:
                        self.lsDI_itemDev[nrDev].dpc.Spi(
                             data["Spi"]["bReset"],
                             data["Spi"]["frequency"],
                             data["Spi"]["chDIOClock"],
                             data["Spi"]["chDIOData"],
                             data["Spi"]["chDIOCS"],
                             data["Spi"]["csIdle"],
                             data["Spi"]["dataMode"],
                             data["Spi"]["format"],
                             data["Spi"]["bRead"],
                             data["Spi"]["nrCnt"],
                             data["Spi"]["bWrite"],
                             data["Spi"]["idle"],
                             data["Spi"]["data"]
                             )
                        return
                    if dFlags["I2c"]:
                        self.lsDI_itemDev[nrDev].dpc.I2c(
                             data["I2c"]["bReset"],
                             data["I2c"]["frequency"],
                             data["I2c"]["bNak"],
                             data["I2c"]["bClear"],
                             data["I2c"]["bStretch"],
                             data["I2c"]["bRead"],
                             data["I2c"]["bWrite"],
                             data["I2c"]["bSpy"],
                             data["I2c"]["nrCnt"],
                             data["I2c"]["chDIOScl"],
                             data["I2c"]["chDIOSda"],
                             data["I2c"]["timeout"],
                             data["I2c"]["data"]
                             )
                        return
                    if dFlags["Can"]:
                        self.lsDI_itemDev[nrDev].dpc.Can(
                             data["Can"]["bReset"],
                             data["Can"]["frequency"],
                             data["Can"]["bRead"],
                             data["Can"]["bWrite"],
                             data["Can"]["chDIOTx"],
                             data["Can"]["chDIORx"],
                             data["Can"]["nrCntRx"],
                             data["Can"]["data"]
                             )
                        return
                    if dFlags["Swd"]:
                        self.lsDI_itemDev[nrDev].dpc.Swd(
                             data["Swd"]["bReset"],
                             data["Swd"]["frequency"],
                             data["Swd"]["chDIOCk"],
                             data["Swd"]["chDIOIo"],
                             data["Swd"]["bPark"],
                             data["Swd"]["bNak"],
                             data["Swd"]["bIdle"],
                             data["Swd"]["bClear"],
                             data["Swd"]["bRead"],
                             data["Swd"]["bWrite"],
                             data["Swd"]["data"]
                             )
                        return
            
        except ErrorWpFnGenericInstrument as err:
            print(err)

    def queryErrList(self):
        pass

    def connect(self,
                nrDev : int
                ):
        """
        @Description
        In case automatic connection is not selected,
        connect to a device using this method.
        @Param
        nrDev : id of device to be attatched to
        @Return
        None
        @Notes
        Use this method to connect to a certain device
        from lsDevsToUse. One of ideas that this wrapper
        offers is to use multiple devices, 2x AD3, 1x ADP2230,
        for example, to get data and process it in a
        centralized module (this lib).
        """
        iretVal = self.lsDevsToUse[nrDev].WpDwfDeviceOpen(
                    c_int(nrDev),
                    self.lsDevsToUse[nrDev].crHwnd
                  )
        if iretVal == wdsc.WP_DWFERROR:
            self.lsDevsToUse[nrDev].lsErrContent.insertErr(
                "Could not connect to <" + str(nrDev) + "> [dev]"
            )

    def disconnect(self,
                   nrDev : int
                   ):
        """
        @Description
        Detach a certain device from current instance of wrapper
        @Param
        nrDev : id of device to be detached from host
        @Return
        None
        @Notes
        Py module can manipulate multiple devices without
        relying on a thread safe usb-driver or library (dwf.dll)
        functionality to manage multiple instances.
        """
        iretVal = self.lsDevsToUse[nrDev].WpDwfDeviceClose(
                    self.lsDevsToUse[nrDev].crHwnd
                  )
        if iretVal == wdsc.WP_DWFERROR:
            self.lsDevsToUse[nrDev].lsErrContent.insertErr(
                "Device: <" + str(nrDev) + "> could not be closed"
            )
