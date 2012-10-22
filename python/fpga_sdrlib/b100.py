"""
Synthesise a QA module into the B100 FPGA.
"""

import os
import shutil
import subprocess


from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib.config import uhddir, miscdir, fpgaimage_fn

b100dir = os.path.join(uhddir, 'fpga', 'usrp2', 'top', 'B100')
    
def make_make(name, inputfiles):
    output_fn = os.path.join(b100dir, 'Make.B100_{name}'.format(name=name))
    template_fn = 'Make.B100_qa.t'
    env = Environment(loader=FileSystemLoader(miscdir))
    template = env.get_template(template_fn)
    f_out = open(output_fn, 'w')
    f_out.write(template.render(name=name, inputfiles=inputfiles))
    f_out.close()

def synthesise(name):
    # Synthesise
    currentdir = os.getcwd()
    os.chdir(b100dir)
    builddir = os.path.join(b100dir, 'build-B100_{0}'.format(name))
    if os.path.exists(builddir):
        shutil.rmtree(builddir)
    logfile_fn = os.path.join(b100dir, 'Make.B100_{0}.log'.format(name))
    logfile = open(logfile_fn, 'w')
    p = subprocess.Popen(['make', '-f', 'Make.B100_{0}'.format(name)],
                         stdout=logfile, stderr=logfile)
    p.wait()
    logfile.flush()
    logfile.close()
    # Check if last line is
    # All constraints were met
    f = open(logfile_fn, 'r')
    lines = f.readlines()
    import pdb
    pdb.set_trace()
    lastline = lines[-2]
    if lastline != 'All constraints were met.\n':
        raise StandardError("Synthesis failed: see {0}".format(logfile_fn))
    f.close()

def copy_image(name):
    # Copy it to where UHD will find it
    builddir = os.path.join(b100dir, 'build-B100_{0}'.format(name))
    shutil.copyfile(os.path.join(builddir, 'B100.bin'), fpgaimage_fn)
