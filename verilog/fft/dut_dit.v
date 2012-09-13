// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is simply a wrapper around the dit module so that it can be accessed from the
// myhdl test bench.

module dut_dit;
   reg                          clk;
   reg                          rst_n;
   reg [`X_WDTH*2-1:0]          in_data;
   wire [`X_WDTH*2-1:0]         out_data;
   reg                          in_nd;
   wire                         out_nd;
   reg [`M_WDTH-1:0]            in_m;
   wire [`M_WDTH-1:0]           out_m;
   wire                         first;
   wire                         error;
   
   initial begin
	  $from_myhdl(clk, rst_n, in_data, in_nd, in_m);
	  $to_myhdl(out_data, out_nd, out_m, first, error);
   end
   
   dit #(`N, `NLOG2, `X_WDTH, `TF_WDTH, `M_WDTH) dut (clk, rst_n, in_data, in_nd, in_m, out_data, out_nd, out_m, first, error);
   
endmodule  