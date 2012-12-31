"""
Utility functions to help with generation and verification of
verilog fft code.
"""

import cmath
import os

from fpga_sdrlib import config
from fpga_sdrlib.conversions import cs_to_dicts
from fpga_sdrlib.generate import copyfile, logceil, format_template

def fft_length_template(pck, fn, dependencies, extraargs={}):
    fft_length = extraargs.get('N', None)
    if fft_length is None:
        raise ValueError("N for stage_to_stage.v is not known.")
    template_dict = {'N': fft_length}
    assert(fn[-4:] == '.v.t')
    ss_fn = fn[:-4] + "_" + str(fft_length) + '.v'
    in_fn = os.path.join(config.verilogdir, pck, fn)
    out_fn = os.path.join(config.builddir, pck, ss_fn)
    out_dir = os.path.join(config.builddir, pck)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    format_template(in_fn, out_fn, 
                    template_dict)
    out_extraargs = {}
    for d in dependencies:
        out_extraargs[d] = extraargs
    return out_fn, out_extraargs

def make_twiddlefactors(pck, fn, dependencies, extraargs={}):
    # dependencies is not used
    fft_length = extraargs.get('N', None)
    width = extraargs.get('width', None)
    if fft_length is None:
        raise ValueError("N for twiddlefactors.v is not known.")
    if width is None:
        raise ValueError("width for twidlefactors.v is not known.")
    vs = [cmath.exp(-i*2j*cmath.pi/fft_length) for i in range(0, fft_length/2)]
    tfs = cs_to_dicts(vs, width, clean1=False)
    tf_dict = {
        'N': fft_length,
        'log_N': logceil(fft_length),
        'width': width,
        'tfs': tfs,
        }
    assert(fn == 'twiddlefactors.v.t')
    twiddlefactors_fn = 'twiddlefactors_{0}.v'.format(fft_length)
    in_fn = os.path.join(config.verilogdir, pck, fn)
    out_fn = os.path.join(config.builddir, pck, twiddlefactors_fn)
    out_dir = os.path.join(config.builddir, pck)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    format_template(in_fn, out_fn, 
                    tf_dict)
    return out_fn, {}

blocks = {
    # The basic modules.
    'butterfly.v': (('fpgamath/multiply_complex.v', 'message/message_slicer.v', 'message/smaller.v'), copyfile, {}),
    'twiddlefactors.v.t': (None, make_twiddlefactors, {}),
    'mstore.v': (None, copyfile, {}),
    'stage.v': (None, copyfile, {}),
    'buffer_BB_to_stage.v': (None, copyfile, {}),
    'stage_to_stage.v.t': (('butterfly.v', 'twiddlefactors.v.t',), fft_length_template, {}),
    'stage_to_out.v': (None, copyfile, {}),
    'dit_series.v.t': (('stage.v', 'buffer_BB_to_stage.v', 'stage_to_out.v',
                        'stage_to_stage.v.t', 'flow/buffer_BB.v'),
                       fft_length_template, {}),
    # qa_contents modules
    'qa_butterfly.v':(('butterfly.v', ), copyfile, {}), 
    'qa_stage.v': (('stage.v', 'buffer_BB_to_stage.v',
                    'stage_to_out.v', 'flow/buffer_BB.v'), copyfile, {}),
    'qa_stage_to_stage.v.t': (('stage.v', 'buffer_BB_to_stage.v',
                    'stage_to_stage.v.t', 'stage_to_out.v', 'flow/buffer_BB.v'), fft_length_template, {}),
    'qa_dit_series.v.t': (('dit_series.v.t',), fft_length_template, {}),
    }

# compatible with running on the B100
compatibles = {
    'butterfly':
        ('qa_butterfly.v', 'uhd/qa_wrapper.v'),
    'dit_series': 
        ('qa_dit_series.v.t', 'uhd/qa_wrapper.v',),
    'stage':
        ('qa_stage.v', 'uhd/qa_wrapper.v',),
    'stage_to_stage':
        ('qa_stage_to_stage.v.t', 'uhd/qa_wrapper.v',),
}

# Not compatible with running on the B100
incompatibles = {
    'butterfly_inner':
        ('qa_butterfly.v', 'uhd/dut_qa_contents.v'),
    'dit_series_inner': 
        ('qa_dit_series.v.t', 'uhd/dut_qa_contents.v'),
    'stage_inner':
        ('qa_stage.v', 'uhd/dut_qa_contents.v',),
    'stage_to_stage_inner':
        ('qa_stage_to_stage.v.t', 'uhd/dut_qa_contents.v',),
}
