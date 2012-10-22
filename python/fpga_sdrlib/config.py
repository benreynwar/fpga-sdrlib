# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import logging
import os
from os.path import dirname

uhddir = os.path.join('/', 'home', 'ben', 'Code', 'uhd')
fpgaimage_fn = "/usr/local/share/uhd/images/usrp_b100_fpga.bin"
basedir = dirname(dirname(dirname(__file__)))
miscdir = os.path.join(basedir, 'misc')
verilogdir = os.path.join(basedir, 'verilog')
builddir = os.path.join(basedir, 'build')

def setup_logging(level):
    "Utility function for setting up logging."
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    # Which packages do we want to log from.
    packages = ('__main__', 'fpga_sdrlib',)
    for package in packages:
        logger = logging.getLogger(package)
        logger.addHandler(ch)
        logger.setLevel(level)
    # Warning only packages
    packages = []
    for package in packages:
        logger = logging.getLogger(package)
        logger.addHandler(ch)
        logger.setLevel(logging.WARNING)
        
