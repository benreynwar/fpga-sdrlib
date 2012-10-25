fpga_sdrlib is a collection of verilog modules for software-defined radios.

It is a work in progress.  None of the included modules in their
current state have been verified on an FPGA.

A python package is included which is used for the generation of
verilog files that require templating and for the verification of the modules
using MyHDL.

Currently it contains three subsections:
  fft - A radix-2 FFT module.
  filterbank - A generic filterbank module.
  channelizer - A module for polyphase-filterbank channelization.

The modules function have been verified in icarus verilog.

Getting them synthesising correctly and verified on the FPGA in the USRP B100 is in progress.
