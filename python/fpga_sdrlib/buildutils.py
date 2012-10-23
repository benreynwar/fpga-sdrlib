import shutil
import os

from jinja2 import Environment, FileSystemLoader

from fpga_sdrlib import config

def copyfile(directory, name):
    out_fn = os.path.join(config.builddir, directory, name)
    shutil.copyfile(os.path.join(config.verilogdir, directory, name), out_fn)
    return out_fn
                    

def format_template(directory, template_name, output_name, template_args):
    """
    Formats a template.
    """
    template_fn = os.path.join(directory, template_name)
    output_fn = os.path.join(config.builddir, directory, output_name)
    env = Environment(loader=FileSystemLoader(config.verilogdir))
    template = env.get_template(template_fn)
    f_out = open(output_fn, 'w')
    f_out.write(template.render(**template_args))
    f_out.close()    
    return output_fn

