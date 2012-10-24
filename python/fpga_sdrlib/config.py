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

default_sendnth = 4
default_defines = {"DEBUG": False,
                   "WIDTH": 32,
                   "MWIDTH": 1}

msg_width = 33
msg_length_width = 10
msg_formatcode_width = 5
msg_modulecode_width = 10
msg_errorcode_width = 7
msg_options = []
msg_options.append("-DMSG_WIDTH={msg_width}")
msg_options.append("-DMSG_LENGTH_WIDTH={msg_length_width}")
msg_options.append("-DMSG_FORMATCODE_WIDTH={msg_formatcode_width}")
msg_options.append("-DMSG_MODULECODE_WIDTH={msg_modulecode_width}")
msg_options.append("-DMSG_ERRORCODE_WIDTH={msg_errorcode_width}")
msg_options = ' '.join(msg_options)
msg_options = msg_options.format(
    msg_width=msg_width,
    msg_length_width=msg_length_width,
    msg_formatcode_width=msg_formatcode_width,
    msg_modulecode_width=msg_modulecode_width,
    msg_errorcode_width=msg_errorcode_width)

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
        
