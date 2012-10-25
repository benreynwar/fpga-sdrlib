# Copyright (c) 2012 Ben Reynwar
# Released under MIT License (see LICENSE.txt)

"""
Functions to convert between complex numbers and integers.

All complex numbers components must be between -1 and 1.

The real component goes to the high bits of the integer and the imaginary
component to the low bits.

"""

def c_to_int(c, x_width):
    """
    Takes a complex number and a width.
    Converts to an integer of length x_width*2 bits.
    """
    # Real part in high x_width bits.
    # Imag part in low x_width bits.
    # Complex components must be between -1 and 1.
    i = f_to_int(c.real, x_width)
    q = f_to_int(c.imag, x_width)
    return i * pow(2, x_width) + q

def cs_to_int(cs, x_width):
    """
    Takes a list of complex numbers and a width.
    Converts to an integer of length (x_width*2*len(C)) bits.
    """
    multipler = 1
    combined = 0
    for c in cs:
        combined += multipler * c_to_int(c, x_width)
        multipler *= pow(2, 2*x_width)
    return combined

def int_to_cs(k, x_width, N):
    """
    Takes a integer, a width, and the number of complex numbers.
    Returns a list of complex numbers.
    """
    cs = []
    for n in range(0, N):
        kb = k % pow(2, 2*x_width)
        cs.append(int_to_c(kb, x_width))
        k = k >> 2*x_width
    return cs

def int_to_c(k, x_width):
    """
    Takes an integer and a width and returns a complex number.
    """
    ik = k >> x_width
    qk = k % pow(2, x_width)
    maxint = pow(2, x_width)-1
    i = int_to_f(ik, x_width)
    q = int_to_f(qk, x_width)
    return i + (0+1j)*q

def f_to_sint(f, x_width, clean1=False):
    """
    Takes a float and returns a signed integer.
    
    If clean1 is True then we scale so that 1 in binary is
    0100000 rather than 0111111.
    This allows a multiplication by 1 followed by a down shift
    to leave the result unchanged.OB
    """
    if f < -1 or f > 1:
        raise ValueError("The tap must be between -1 and 1.")
    if clean1 is False:
        maxint = pow(2, x_width-1)-1
    else:
        maxint = pow(2, x_width-2)
    i = int(round(f*maxint))
    return i

def sint_to_int(si, width):
    """
    Converts a signed integer to a two complement integer.
    """
    if si >=0:
        return si
    else:
        return si + pow(2, width)

def f_to_int(f, width, clean1=False):
    return sint_to_int(f_to_sint(f, width, clean1), width)

def sint_to_f(si, width):
    maxint = pow(2, width-1)-1
    return float(si)/maxint

def int_to_sint(i, width):
    middleint = pow(2, width)/2
    if i >= middleint:
        i -= pow(2, width)
    return i

def int_to_f(i, width):
    return sint_to_f(int_to_sint(i, width), width)

def f_to_istr(width, f):
    """
    f is between 0 and 1.
    If f is 1 we want binary to be 010000000 (maxno).

    Used for generating the twiddle factor module.
    """
    if f < 0 or f > 1:
        raise ValueError("f must be between 0 and 1")
    maxno = pow(2, width-2)
    return str(int(round(f * maxno)))

def is_to_dicts(iis, width):
    """
    Converts a list of integer to a list of dictionaries of with
    attributes (i, sign, value)
    Useful to send to template formatter.
    """
    dicts = []
    for i, ii in enumerate(iis):
        d = {}
        d['i'] = i
        if ii >= 0:
            d['sign'] = ''
        else:
            d['sign'] = '-'
        d['value'] = abs(ii)
        dicts.append(d)
    return dicts

def fs_to_dicts(fs, width, clean1=False):
    """
    Converts a list of floats to a list of dictionaries of with
    attributes (i, sign, value)
    Useful to send to template formatter.
    """
    iis = [f_to_sint(f, width, clean1=clean1) for f in fs]
    return is_to_dicts(iis, width)

def cs_to_dicts(cs, width, clean1=False):
    """
    Converts a list of complex numbers to a list of dictionaries of with
    attributes (i, re_sign, im_sign, re, im)
    Useful to send to template formatter.
    """
    dicts = []
    for i, c in enumerate(cs):
        d = {}
        d['i'] = i
        if c.real > 0:
            d['re_sign'] = ''
        else:
            d['re_sign'] = '-'
            c = -c.real + (0+1j)*c.imag
        if c.imag > 0:
            d['im_sign'] = ''
        else:
            d['im_sign'] = '-'
            c = c.real - (0+1j)*c.imag
        d['re'] = str(f_to_sint(c.real, width/2, clean1=clean1))
        d['im'] = str(f_to_sint(c.imag, width/2, clean1=clean1))
        
        dicts.append(d)
    return dicts
    
