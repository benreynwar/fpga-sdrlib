"""
Generates some wrapper QA files for use with testing on a USRP.
"""

def copyfile(pck, fn):
    # Put inside to avoid circular dependency
    from fpga_sdrlib.buildutils import copyfile as cf
    return cf(pck,fn)

blocks = {
    'dut_qa_wrapper.v': (None, copyfile, {}),
    'qa_wrapper_null.v': (None, copyfile, {}),
    }

compatibles = {
    'null': ('qa_wrapper_null.v',),
    }
incompatibles = {}
