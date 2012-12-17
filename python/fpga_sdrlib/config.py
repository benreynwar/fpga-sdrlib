# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import logging
import os
import math
from copy import copy
from os.path import dirname

def logceil(n):
    val = int(math.ceil(float(math.log(n))/math.log(2)))
    # To keep things simple never return 0.
    # Declaring reg with 0 length is not legal.
    if val == 0:
        val = 1
    return val

uhddir = os.path.join('/', 'home', 'ben', 'Code', 'uhd')
fpgaimage_fn = "/usr/local/share/uhd/images/usrp_b100_fpga.bin"
basedir = dirname(dirname(dirname(__file__)))
miscdir = os.path.join(basedir, 'misc')
verilogdir = os.path.join(basedir, 'verilog')
builddir = os.path.join(basedir, 'build')

default_sendnth = 4
default_width = 32
default_mwidth = 1
default_debug = False
default_log_sendnth = 6
errorcode = 666
msg_width = 32
msg_length_width = 10
msg_formatcode_width = 4
msg_modulecode_width = 10
msg_errorcode_width = 7
# The buffer size for the msg/sample combiner in qa_wrapper.
default_combiner_buffer_length = 128
# How many bits to chop off real numbers in the complex stream
# so that we get some header bits.
msg_shift = 1

default_defines = {
    "DEBUG": default_debug,
    "WIDTH": default_width,
    "MWIDTH": default_mwidth,
    "ERRORCODE": errorcode,
    'MSG_WIDTH': msg_width,
    'MSG_LENGTH_WIDTH': msg_length_width,
    'MSG_FORMATCODE_WIDTH': msg_formatcode_width,
    'MSG_MODULECODE_WIDTH': msg_modulecode_width,
    'MSG_ERRORCODE_WIDTH': msg_errorcode_width,
    'MSG_SHIFT': msg_shift,
    'LOG_SENDNTH': default_log_sendnth,
    'COMBINER_BUFFER_LENGTH': default_combiner_buffer_length,
    'LOG_COMBINER_BUFFER_LENGTH': logceil(default_combiner_buffer_length),
    'MAX_PACKET_LENGTH': pow(2, msg_formatcode_width)-1,
    }

def updated_defines(updates):
    defines = copy(default_defines)
    defines.update(updates)
    return defines

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
        
