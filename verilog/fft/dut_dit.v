// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is simply a wrapper around the dit module so that it can be accessed from the
// myhdl test bench.

module dut_dit;
   reg                          clk;
   reg                          rst_n;
   reg [`WIDTH-1:0]             in_data;
   wire [`WIDTH-1:0]          out_data;
   reg                          in_nd;
   wire                         out_nd;
   reg [`MWIDTH-1:0]           in_m;
   wire [`MWIDTH-1:0]          out_m;
   wire                         first;
   wire                         error;
   
   initial begin
	  $from_myhdl(clk, rst_n, in_data, in_nd, in_m);
	  $to_myhdl(out_data, out_nd, out_m, first, error);
   end
   
   dit #(`N, `LOG_N, `WIDTH/2, `WIDTH/2, `MWIDTH) dut
     (clk, rst_n, in_data, in_nd, in_m, out_data, out_nd, out_m, first, error);
   
endmodule  