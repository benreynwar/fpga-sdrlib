import os
import math
import shutil
import logging

from sdrlib.fft.build import generate as generate_fft
from sdrlib.filterbank.build import generate as generate_fb
from sdrlib import config

logger = logging.getLogger(__name__)

def generate(name, n_chans, taps, width, mwidth):
    """
    Generate the fft files to perform an fft.
    
    Args:
        n_chans: Number of channels to split into.
        taps: The taps to use for the channelizer.
        width: Number of bits in a complex number.
        mwidth: Number of bits in meta data.
    """
    logn = math.log(n_chans)/math.log(2)
    if int(logn) != logn:
        raise ValueError("Number of channels must be a power of two.")
    logn = int(logn)
    extra_taps = int(math.ceil(1.0*len(taps)/n_chans)*n_chans - len(taps))
    taps = taps + [0] * extra_taps
    # Make taps for each channel
    chantaps = [list(reversed(taps[i: len(taps): n_chans])) for i in range(0, n_chans)]
    for taps in chantaps:
        summedtaps = sum(taps)
        if summedtaps < -1 or summedtaps > 1:
            raise ValueError("Summed taps for each channel must be between -1 and 1 (Value is {0}).".format(summedtaps))
    flt_len = len(chantaps[0])
    chan_builddir= os.path.join(config.builddir, 'channelizer')
    if not os.path.exists(chan_builddir):
        os.makedirs(chan_builddir)
    dut_channelizer_fn = os.path.join(chan_builddir, 'dut_channelizer.v')
    shutil.copyfile(os.path.join(config.verilogdir, 'channelizer', 'dut_channelizer.v'),
                    dut_channelizer_fn)
    channelizer_fn = os.path.join(chan_builddir, 'channelizer.v')
    shutil.copyfile(os.path.join(config.verilogdir, 'channelizer', 'channelizer.v'),
                    channelizer_fn)
    executable_fft, inputfiles_fft = generate_fft(n_chans, width/2, mwidth)
    executable_fb, inputfiles_fb = generate_fb(name, chantaps, width, mwidth)
    inputfiles = inputfiles_fft + inputfiles_fb + [channelizer_fn]
    inputfilestr = ' '.join(inputfiles) + ' ' + dut_channelizer_fn
    executable = 'channelizer_{name}'.format(name=name)
    executable = os.path.join(chan_builddir, executable)
    cmd = ("iverilog -o {executable} -DN={n} -DWDTH={width} -DMWDTH={mwidth} "
           "-DLOGN={logn} -DFLTLEN={flt_len} {inputfiles}"
           ).format(n=n_chans, width=width, mwidth=mwidth, logn=logn,
                    flt_len=flt_len, executable=executable,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable, inputfilestr

