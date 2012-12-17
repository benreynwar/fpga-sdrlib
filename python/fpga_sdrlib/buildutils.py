import shutil
import os
import logging
import filecmp

from fpga_sdrlib import config
from fpga_sdrlib import message, uhd, flow, flter, fpgamath
from fpga_sdrlib import b100

logger = logging.getLogger(__name__)

def make_define_string(defines):
    definestrs = []
    for k, v in defines.items():
        if v is True or v is False:
            if v is True:
                definestrs.append("-D" + k)
        else:
            definestrs.append("-D{0}={1}".format(k, v))
    return ' '.join(definestrs)

def generate_block(package, filename, extraargs={}, included_dependencies=set(),
                   include_filenames=[]):
    included_dependencies.add((package, filename))
    dependencies, generating_function, args = blocks[package][filename]
    if dependencies is None:
        dependencies = []
    include_filename, dep_extraargs = generating_function(
        package, filename, dependencies, extraargs, **args)
    include_filenames.append(include_filename)
    if dependencies is None:
        dependencies = []
    if args is None:
        args = {}
    for d in dependencies:
        bits = d.split('/')
        if len(bits) == 1:
            pck = package
            fn = bits[0]
        else:
            pck = bits[0]
            fn = bits[1]
        if d in dep_extraargs:
            extraargs = dep_extraargs[d]
        else:
            extraargs = {}
        if (pck, fn) not in included_dependencies:
            generate_block(pck, fn, extraargs, included_dependencies, include_filenames)
    return included_dependencies, include_filenames

def d2pd(package, dependency):
    bits = dependency.split('/')
    if len(bits) == 1:
        pck = package
        fn = bits[0]
    else:
        pck = bits[0]
        fn = bits[1]
    return (pck, fn)

def pd2fn(pck, fn):
    return os.path.join(config.verilogdir, pck, fn)
    
def generate_B100_image(package, name, suffix, defines=config.default_defines, extraargs={}):
    builddir = os.path.join(config.builddir, package)
    outputdir = os.path.join(builddir, 'build-B100_{name}{suffix}'.format(
            name=name, suffix=suffix))
    vdir = os.path.join(builddir, 'verilog-B100_{name}{suffix}'.format(
            name=name, suffix=suffix))
    if not os.path.exists(vdir):
        os.makedirs(vdir)
    dependencies = compatibles[package][name]
    included_dependencies = set()
    inputfiles = [os.path.join(pd2fn('uhd', 'u1plus_core_QA.v'))]
    for d in dependencies:
        pck, fn = d2pd(package, d)
        if (pck, fn) not in included_dependencies:
            generate_block(pck, fn, extraargs, included_dependencies, inputfiles)
    new_inputfiles= []
    changed = False
    for f in inputfiles:
        # Prefix the macros to the beginning of each file.
        # FIXME: There has to be a better way to get this working :(.
        assert(f.endswith('.v'))
        bn = os.path.basename(f)
        f2 = os.path.join(vdir, bn[:-2] + '_prefixed.v')
        f3 = os.path.join(vdir, bn[:-2] + '_final.v')
        shutil.copyfile(f, f2)
        b100.prefix_defines(f2, defines)
        # See if any of the produced files are different than what
        # was used last time.
        if (not os.path.exists(f3)) or (not filecmp.cmp(f2, f3)):
            changed = True
            shutil.copyfile(f2, f3)
        new_inputfiles.append(f3)
    image_fn = os.path.join(outputdir, 'B100.bin')
    if changed or not os.path.exists(image_fn):
        b100.make_make(name+suffix, builddir, new_inputfiles, defines)
        return b100.synthesise(name+suffix, builddir)
    else:
        return image_fn

def generate_icarus_executable(package, name, suffix, defines=config.default_defines, extraargs={}):
    builddir = os.path.join(config.builddir, package)
    if name in compatibles[package]:
        dependencies = compatibles[package][name]
        dependencies = list(dependencies)
        dependencies.append('uhd/dut_qa_wrapper.v')
    else:
        dependencies = incompatibles[package][name]        
    included_dependencies = set()
    inputfiles = []
    for d in dependencies:
        pck, fn = d2pd(package, d)
        if (pck, fn) not in included_dependencies:
            generate_block(pck, fn, extraargs, included_dependencies, inputfiles)
    inputfilestr = ' '.join(inputfiles)
    print(inputfilestr)
    executable = name + suffix
    executable = os.path.join(builddir, executable)
    definestr = make_define_string(defines)
    cmd = ("iverilog -o {executable} {definestr} {inputfiles}"
           ).format(executable=executable,
                    definestr=definestr,
                    inputfiles=inputfilestr)
    logger.debug(cmd)
    os.system(cmd)
    return executable

packages = {'message': message,
           'uhd': uhd,
           'flow': flow,
           'flter': flter,
           'fpgamath': fpgamath,
           }

blocks = dict([(key, getattr(sp, 'blocks')) for
               key, sp in packages.items()])

compatibles = dict([(key, getattr(sp, 'compatibles')) for
                    key, sp in packages.items()])

incompatibles = dict([(key, getattr(sp, 'incompatibles')) for
                      key, sp in packages.items()])

