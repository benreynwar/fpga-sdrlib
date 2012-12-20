fpga_sdrlib is a collection of verilog modules for software-defined radios.

This framework is not yet documented well enough that it'll be easy to use for
anyone but me.  However if you do want to have a play with it then:
 - Requirements: python, UHD source, GNU Radio, MyHDL, Icarus Verilog and quite
     possibly some other python packages. 
 - update fpga_sdrlib/python/fpga_sdrlib/config.py
   uhddir needs to be set to the location of the uhd source
   fpgaimag_fn should be the location the USRP looks for the FPGA image and the file
     should be writable.

The subsections are:
  uhd - Wrappers to insert modules into the B100 FPGA.
  fpgamath - Utility math modules.
  flow - Modules that change the flow of data (currently a buffer and splitter).
  message - Modules for combining and separating message and data streams.
  flter - Filter modules.
  fft - FFT modules (currently not working). 
  channelizer - A module for polyphase-filterbank channelization (currently not working).

Building and Testing:
  The framework contains python code to automate the process of
  building and testing.  For example fpga_sdrlib/verilog/flter
  contains the verilog code for filter modules and
  fpga_sdrlib/python/fpga_sdrlib/flter contains the python code for
  building and testing the flter modules.  In particular qa_flter.py
  uses the python unit-testing framework to test the modules with
  MyHDL and Icarus, synthesise each module into the B100 FPGA code,
  update the FPGA image, and then test the image on the B100.  The
  B100 image is modified for testing so that data flows into the B100
  through the transmit chain, through the module under test and then
  back along the receive chain.

The interface for a typical module is:
Inputs:
  clk:          clock signal
  rst_n:        reset when low
  in_data:      a complex input
  in_m:         meta_data synchronous with in_data
  in_nd:        high if new data is in in_data
  in_msg_data:  message stream data
  in_msg_nd:    high if new message stream data is in in_msg_data
Outputs:
  out_data:     a complex output
  out_m:        meta_data synchronous with out_data
  out_nd:       high if new data is in in_data
  out_msg_data: message stream data
  out_msg_nd:   high if new message stream data is in out_msg_data
  error:        high if an error has occured

The idea behind the message streams is that they can be used for
things like setting taps or returning debug messages.

Currently when using a B100 the message streams are sent and received
with the complex data stream by reducing the complex numbers from 32
bits to 30 bits and using one of the extra bits to indicate a message
packet header.

It's not a pretty solution but it seems to work.
