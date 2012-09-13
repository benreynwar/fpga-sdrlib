# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import cmath
import math
import os
import logging
import shutil

from jinja2 import Environment, FileSystemLoader

from sdrlib import config

logger = logging.getLogger(__name__)

def generate(N, width, mwidth):
    """
    Generate the fft files to perform an fft.
    
    Args:
        N: Length of the FFT.
        width: Number of bits in a real number.  Complex is twice this.
        mwidth: Number of bits in data passed through.
    """
    logN = math.log(N)/math.log(2)
    if (logN != int(logN)):
        raise ValueError("N must be a power of 2.")
    logN = int(logN)
    make_twiddlefactor(N, width)
    inputfiles = ['dit.v', 'butterfly.v']
    for f in inputfiles:
        shutil.copyfile(os.path.join(config.verilogdir, 'fft', f),
                        os.path.join(config.builddir, 'fft', f))
    executable = "fft_{n}_{x_width}_{tf_width}".format(
        n=N, x_width=width, tf_width=width)
    executable = os.path.join(config.builddir, 'fft', executable)
    inputfiles.append('twiddlefactors_{n}.v'.format(n=N))
    inputfiles = [os.path.join(config.builddir, 'fft', f) for f in inputfiles]
    inputfilestr = ' '.join(inputfiles + [os.path.join(config.builddir, 'fft', 'dut_dit.v')])
    cmd = ("iverilog -o {executable} -DN={n} -DX_WDTH={x_width} -DNLOG2={nlog2} "
           "-DTF_WDTH={tf_width} -DM_WDTH={mwidth} "
           "{inputfiles} "
           ).format(executable=executable, n=N, x_width=width, mwidth=mwidth,
                    tf_width=width, nlog2=logN, inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable, inputfiles
           
           
def f_to_istr(width, f):
    """
    f is between 0 and 1.
    If f is 1 we want binary to be 010000000 (maxno).

    Used for generating the twiddle factor module.
    """
    if f < 0 or f > 1:
        raise ValueError("f must be between 0 and 1")
    maxno = pow(2, width-2)
    return str(int(round(f * maxno)))

def make_twiddlefactor(N, tf_width, template_fn=None, output_fn=None):
    """
    Generates a verilog file containing a twiddle factor module from a template file.
    """
    if template_fn is None:
        template_fn = os.path.join('fft', 'twiddlefactors.v.t')
    if output_fn is None:
        output_fn = os.path.join(config.builddir, 'fft', 'twiddlefactors_{0}.v'.format(N))
    env = Environment(loader=FileSystemLoader(config.verilogdir))
    template = env.get_template(template_fn)
    Nlog2 = int(math.log(N, 2))
    tfs = []
    for i in range(0, N/2):
        tf = {}
        tf['i'] = i
        v = cmath.exp(-i*2j*cmath.pi/N)
        if v.real > 0:
            tf['re_sign'] = ''
        else:
            tf['re_sign'] = '-'
            v = -v.real + (0+1j)*v.imag
        if v.imag > 0:
            tf['im_sign'] = ''
        else:
            tf['im_sign'] = '-'
            v = v.real - (0+1j)*v.imag
        tf['re'] = f_to_istr(tf_width, v.real)
        tf['im'] = f_to_istr(tf_width, v.imag)
        tfs.append(tf)
    if not os.path.exists(os.path.dirname(output_fn)):
        os.makedirs(os.path.dirname(output_fn))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(tf_width=tf_width, tfs=tfs, Nlog2=Nlog2))    
    f_out.close()
    

