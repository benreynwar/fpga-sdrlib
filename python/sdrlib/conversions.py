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

def f_to_sint(f, x_width):
    """
    Takes a float and returns a signed integer.
    """
    if f < -1 or f > 1:
        raise ValueError("The tap must be between -1 and 1.")
    maxint = pow(2, x_width-1)-1
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

def f_to_int(f, width):
    return sint_to_int(f_to_sint(f, width), width)

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
