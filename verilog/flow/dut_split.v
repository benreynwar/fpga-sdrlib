// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is simply a wrapper around the split module
// so that it can be accessed from the myhdl test bench.

module dut_split;
   reg                              clk;
   reg                              reset;
   reg [`WIDTH-1:0]                 in_data;
   wire [`WIDTH*`N_OUT_STREAMS-1:0] out_data;
   reg                              in_nd;
   wire                             out_nd;
   wire                             error;

   wire                             rst_n;
   assign rst_n = ~reset;
   initial begin
	  $from_myhdl(clk, reset, in_data, in_nd);
	  $to_myhdl(out_data, out_nd, error);
   end
   
   split
     #( `N_OUT_STREAMS, `LOG_N_OUT_STREAMS, `WIDTH)
   dut
     (clk, rst_n, in_data, in_nd, out_data, out_nd);
   
endmodule  