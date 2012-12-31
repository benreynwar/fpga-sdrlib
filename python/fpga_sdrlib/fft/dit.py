"""
Python implementation of FFT to test verilog against.
"""
import math
import cmath

def pystage(N, start_index, in_data):
    assert(len(in_data) == N)
    tfs = [cmath.exp(-i*2j*cmath.pi/N) for i in range(0, N/2)]
    tfs = tfs
    out_data = [None]*N
    # S is number of interleaved transforms.
    S = N/2/pow(2,start_index)
    for out_addr0 in range(N/2):
        # out_addr0 = kS + j
        out_addr1 = out_addr0 + N/2
        k = out_addr0 // S
        j = out_addr0 % S
        in_addr0 = 2*k*S + j
        in_addr1 = 2*k*S + S + j
        tf_addr = k*S
        W = tfs[tf_addr]
        A = in_data[in_addr0]
        B = in_data[in_addr1]
        C = A + B*W
        D = A - B*W
        out_data[out_addr0] = C
        out_data[out_addr1] = D
    return out_data

def pyditfft(data):
    N = len(data)
    log_N = math.log(N)/math.log(2)
    if log_N != int(log_N):
        raise ValueError("len(data) must be a power of 2")
    log_N = int(log_N)
    for i in range(log_N):
        data = pystage(N, i, data)
    return data

if __name__ == '__main__':
    import random
    n_data = 16
    data = [random.random()*2-1 + random.random()*2j-1j for i in range(n_data)]
    from numpy import fft
    ee = fft.fft(data)
    rr = pyditfft(data)
    assert(len(ee) == len(rr))
    tol = 1e-6
    for e, r in zip(ee, rr):
        assert(abs(e-r) < tol)
