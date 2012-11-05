"""
Synthesise a QA module into the B100 FPGA.
"""

import os
import shutil
import subprocess


from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib import config
from fpga_sdrlib.config import uhddir, miscdir, fpgaimage_fn

b100dir = os.path.join(uhddir, 'fpga', 'usrp2', 'top', 'B100')
custom_src_dir = os.path.join(config.verilogdir, 'uhd')

def make_defines_file(builddir, defines):
    fn = os.path.join(builddir, 'global_defines.vh')
    f = open(fn, 'w')
    f.write(make_defines_prefix(defines))
    f.close
    return fn

def make_defines_prefix(defines):
    lines = []
    for k, v in defines.items():
        lines.append('`define {0} {1}'.format(k, v))
    txt = '\n'.join(lines)
    txt += '\n'
    return txt

def prefix_defines(fn, defines):
    f = open(fn)
    contents = f.read()
    f.close()
    prefix = make_defines_prefix(defines)
    f = open(fn, 'w')
    f.write(prefix)
    f.write(contents)
    f.close()

def make_make(name, builddir, inputfiles, defines):
    header = make_defines_file(builddir, defines)
    shutil.copy(header, os.path.join(config.builddir, 'message'))
    inputfiles = [header] + inputfiles
    output_fn = os.path.join(builddir, 'Make.B100_{name}'.format(name=name))
    template_fn = 'Make.B100_qa.t'
    env = Environment(loader=FileSystemLoader(miscdir))
    template = env.get_template(template_fn)
    f_out = open(output_fn, 'w')
    output_dir = os.path.join(builddir, 'build-B100_{name}'.format(name=name))
    custom_defs = []
    for k, v in defines.items():
        if k == 'DEBUG':
            custom_defs.append(k)
        else:
            custom_defs.append("{0}={1}".format(k, v))
    custom_defs = " | ".join(custom_defs)
    f_out.write(template.render(build_dir=output_dir,
                                custom_src_dir=custom_src_dir,
                                inputfiles=inputfiles,
                                #custom_defs=custom_defs,
                                ))
    f_out.close()

def synthesise(name, builddir):
    output_dir = os.path.join(builddir, 'build-B100_{name}'.format(name=name))
    # Synthesise
    currentdir = os.getcwd()
    os.chdir(b100dir)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    make_fn = os.path.join(builddir, 'Make.B100_{0}'.format(name))
    logfile_fn = os.path.join(builddir, 'Make.B100_{0}.log'.format(name))
    logfile = open(logfile_fn, 'w')
    p = subprocess.Popen(['make', '-f', make_fn],
                         stdout=logfile, stderr=logfile)
    p.wait()
    logfile.flush()
    logfile.close()
    # Check if last line is
    # All constraints were met
    f = open(logfile_fn, 'r')
    lines = f.readlines()
    lastline = lines[-2]
    if lastline != 'All constraints were met.\n':
        raise StandardError("Synthesis failed: see {0}".format(logfile_fn))
    f.close()
    os.chdir(currentdir)

