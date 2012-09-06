import os
from os.path import dirname

basedir = dirname(dirname(dirname(__file__)))
verilogdir = os.path.join(basedir, 'verilog')
builddir = os.path.join(basedir, 'build')
