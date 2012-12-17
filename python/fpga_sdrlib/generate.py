import shutil
import os
import math

from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib import config

def logceil(n):
    val = int(math.ceil(float(math.log(n))/math.log(2)))
    # To keep things simple never return 0.
    # Declaring reg with 0 length is not legal.
    if val == 0:
        val = 1
    return val

def copyfile(directory, name, dependencies, extraargs={}):
    in_fn = os.path.join(config.verilogdir, directory, name)
    out_fn = os.path.join(config.builddir, directory, name)
    out_dir = os.path.join(config.builddir, directory)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    shutil.copyfile(in_fn, out_fn)
    dep_extraargs = dict([(d, extraargs) for d in dependencies])
    return out_fn, dep_extraargs

def format_template(template_fn, output_fn, template_args):
    """
    Formats a template.
    """
    env = Environment(loader=FileSystemLoader(config.verilogdir))
    template = env.get_template(os.path.relpath(template_fn, config.verilogdir))
    f_out = open(output_fn, 'w')
    f_out.write(template.render(**template_args))
    f_out.close()

