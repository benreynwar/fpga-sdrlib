// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is simply a wrapper around the message_stream_combiner module
// so that it can be accessed from the myhdl test bench.

module dut_message_slicer;
   reg                          clk;
   reg                          reset;
   reg [`WIDTH*`N_SLICES-1:0]   in_data;
   wire [`WIDTH-1:0]            out_data;
   reg                          in_nd;
   wire                         out_nd;
   wire                         error;
   
   initial begin
	  $from_myhdl(clk, reset, in_data, in_nd);
	  $to_myhdl(out_data, out_nd, error);
   end

   wire rst_n;
   assign rst_n = ~reset;
   
   message_slicer
     #(`N_SLICES, `WIDTH, `BUFFER_LENGTH)
   dut
     (clk, rst_n, in_data, in_nd, out_data, out_nd, error);
   
endmodule  