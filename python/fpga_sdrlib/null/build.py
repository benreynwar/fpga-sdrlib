# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import os
import math
import shutil
import logging

from fpga_sdrlib import config
from fpga_sdrlib import b100
from fpga_sdrlib.uhd.build import generate_qa_wrapper_null_files

logger = logging.getLogger(__name__)

def generate_null_B100_image(name, defines):
    null_builddir= os.path.join(config.builddir, 'null')
    if not os.path.exists(null_builddir):
        os.makedirs(null_builddir)
    inputfiles = generate_qa_wrapper_null_files()
    b100.make_make(name, null_builddir, inputfiles, defines)
    for f in inputfiles:
        b100.prefix_defines(f, defines)
    b100.synthesise(name, null_builddir)
    
