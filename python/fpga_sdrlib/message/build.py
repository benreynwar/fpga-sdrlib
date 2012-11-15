# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

import cmath
import math
import os
import logging
import time

from fpga_sdrlib import config, b100
from fpga_sdrlib.buildutils import copyfile, format_template

logger = logging.getLogger(__name__)


def logceil(n):
    val = int(math.ceil(float(math.log(n))/math.log(2)))
    # To keep things simple never return 0.
    # Declaring reg with 0 length is not legal.
    if val == 0:
        val = 1
    return val

def check_builddir():
    messagebuilddir = os.path.join(config.builddir, 'message')
    if not os.path.exists(messagebuilddir):
        os.makedirs(messagebuilddir)

def generate_stream_combiner_files():
    """
    Generate the files for the message stream combiner.
    """
    check_builddir()
    inputfiles = ['message_stream_combiner.v']
    outputfiles = []
    for f in inputfiles:
        outputfiles.append(copyfile('message', f))
    return outputfiles

def generate_slicer_files():
    """
    Generate the files for the message slicer.
    """
    check_builddir()
    inputfiles = ['message_slicer.v']
    outputfiles = []
    for f in inputfiles:
        outputfiles.append(copyfile('message', f))
    return outputfiles

def generate_sample_msg_splitter_files():
    check_builddir()
    return [copyfile('message', 'sample_msg_splitter.v')]
    
def generate_files():
    return generate_stream_combiner_files() + generate_slicer_files()

def generate_sample_msg_splitter_B100_image(name, defines=config.default_defines):
    message_builddir= os.path.join(config.builddir, 'message')
    inputfiles = generate_sample_msg_splitter_files()
    inputfiles.append(copyfile('message', 'qa_sample_msg_splitter.v'))
    b100.make_make(name, message_builddir, inputfiles, defines)
    for f in inputfiles:
        b100.prefix_defines(f, defines)
    b100.synthesise(name, message_builddir)

def generate_combo_B100_image(name, defines=config.default_defines):
    message_builddir= os.path.join(config.builddir, 'message')
    inputfiles = generate_sample_msg_splitter_files()
    inputfiles += generate_stream_combiner_files()
    inputfiles.append(copyfile('message', 'qa_combo.v'))
    b100.make_make(name, message_builddir, inputfiles, defines)
    for f in inputfiles:
        b100.prefix_defines(f, defines)
    b100.synthesise(name, message_builddir)

def generate_stream_combiner_executable(
    method, n_streams, width, input_buffer_length, max_packet_length):
    """
    Generate an executable for the stream combiner DUT.
    Use for MyHDL testing.
    
    Args:
        method: What are we generating for (icarus or xilinx).
        n_streams: Number of message streams to combine.
        width: Bit width of a data block.
        input_buffer_length: Number of data blocks in each input buffer.
        max_packet_length: Maximum number of data blocks in a packet.
    """
    assert(method in ('icarus', 'xilinx'))
    check_builddir()
    # Check that buffer lengths are power of two
    log_input_buffer_length = math.log(input_buffer_length)/math.log(2)
    if log_input_buffer_length != int(log_input_buffer_length):
        raise ValueError("input_buffer_length must be a power of 2")
    dut_msc_fn = copyfile('message', 'dut_message_stream_combiner.v')
    executable = "message_stream_combiner"
    executable = os.path.join(config.builddir, 'message', executable)
    inputfiles = generate_stream_combiner_files()
    inputfilestr = ' '.join(inputfiles + [dut_msc_fn])
    cmd = ("iverilog -o {executable} -DN_STREAMS={n_streams} -DLOG_N_STREAMS={log_n_streams} "
           "-DWIDTH={width} -DINPUT_BUFFER_LENGTH={input_buffer_length} "
           "-DLOG_INPUT_BUFFER_LENGTH={log_input_buffer_length} "
           "-DMAX_PACKET_LENGTH={max_packet_length} "
           "-DLOG_MAX_PACKET_LENGTH={log_max_packet_length} "
           "{inputfiles} "
           ).format(executable=executable, n_streams=n_streams,
                    log_n_streams=logceil(n_streams),
                    width=width,
                    input_buffer_length=input_buffer_length,
                    log_input_buffer_length=int(log_input_buffer_length),
                    max_packet_length=max_packet_length,
                    log_max_packet_length=logceil(max_packet_length),
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable

def generate_slicer_executable(method, n_slices, width, buffer_length):
    """
    Generate the files for creating message streams.
    
    Args:
        method: What are we generating for (icarus or xilinx).
        n_slices: How many times bigger the input is that width.
        width: Bit width of a data block.
        buffer_length: Number of data blocks in the buffer.
    """
    assert(method in ('icarus', 'xilinx'))
    check_builddir()
    # Check that buffer lengths are power of two
    log_buffer_length = math.log(buffer_length)/math.log(2)
    if log_buffer_length != int(log_buffer_length):
        raise ValueError("buffer_length must be a power of 2")
    dut_ms_fn = copyfile('message', 'dut_message_slicer.v')
    inputfiles = generate_slicer_files()
    executable = "message_slicer"
    executable = os.path.join(config.builddir, 'message', executable)
    inputfiles = [os.path.join(config.builddir, 'message', f) for f in inputfiles]
    inputfilestr = ' '.join(inputfiles + [dut_ms_fn])
    cmd = ("iverilog -o {executable} -DN_SLICES={n_slices} "
           "-DLOG_N_SLICES={log_n_slices} "
           "-DWIDTH={width} -DBUFFER_LENGTH={buffer_length} "
           "-DLOG_BUFFER_LENGTH={log_buffer_length} "
           "{inputfiles} "
           ).format(executable=executable, n_slices=n_slices,
                    log_n_slices=int(math.ceil(math.log(n_slices)/math.log(2))),
                    width=width,
                    buffer_length=buffer_length,
                    log_buffer_length=int(log_buffer_length),
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable

