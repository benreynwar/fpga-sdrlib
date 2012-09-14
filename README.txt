fpga_sdrlib is a collection of verilog modules for software-defined radios.

A python package is included which is used for the generation of
verilog files from templates and for the verifiction of the modules
using MyHDL.

Currently it contains three subsections:
  fft - A radix-2 FFT module.
  filterbank - A generic filterbank module.
  channelizer - A module for polyphase-filterbank channelization.
