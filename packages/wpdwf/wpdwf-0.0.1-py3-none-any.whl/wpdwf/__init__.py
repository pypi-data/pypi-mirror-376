
####################################################
####################################################
###         Project : WF python bindings         ###
###         Engineer : bs                        ###
###         Company : Digilent RO                ###
####################################################
####################################################

"""
Add here the path for __pydynamic__ where .pyd files will be that
are masked, but the interpreter should see them as it sees those in
DLLs.
"""

__version__ = "0.0.1"

WPDWF_VERSION = "wpdwf 0.0.1 Sep 2025"
WPDWF_VERSION_INFO = (0, 0, 1)
WPDWF_VERSION_NUMBER = 0x000001

def IsBitSet(fs : int,
             bit : int
             ) -> int:
    """
    @Description
    Check the features of device's instruments
    by applying a mask on `fs` parameter, `bit`
    is the mask.
    @Parameters
    fs : 32 bit source feature
    bit : 32 bit mask
    @Return
    True or False
    @Notes
    In Python data types are dynamically evaluated,
    it's better to specify them though where dwf lib
    has primarly 32 bit parameters (c_int/int).
    """
    return ((fs & (1 << bit)) != 0)
