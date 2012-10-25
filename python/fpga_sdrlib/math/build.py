import os

from fpga_sdrlib import config
from fpga_sdrlib.buildutils import copyfile

def get_builddir():
    fftbuilddir = os.path.join(config.builddir, 'math')
    if not os.path.exists(fftbuilddir):
        os.makedirs(fftbuilddir)
    return fftbuilddir

def generate_math_files():
    get_builddir()
    inputfiles = []
    inputfiles.append(copyfile('math', 'multiply.v'))
    return inputfiles
