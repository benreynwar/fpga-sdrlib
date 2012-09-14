// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is a wrapper around the channelizer module so that it can be
// accessed from the myhdl test bench.

module dut_channelizer;
   reg                   clk;
   reg                   rst_n;
   reg [`WDTH-1:0]       in_data;
   reg                   in_nd;
   reg [`MWDTH-1:0]      in_m;
   wire [`WDTH-1:0]      out_data;
   wire                  out_nd;
   wire [`MWDTH-1:0]     out_m;
   wire                  error;
   wire                  first_channel;
   
   initial begin
	  $from_myhdl(clk, rst_n, in_data, in_nd, in_m);
	  $to_myhdl(out_data, out_nd, out_m, error, first_channel);
   end

   channelizer #(`N, `LOGN, `WDTH, `MWDTH, `FLTLEN) dut
     (clk, rst_n, in_data, in_nd, in_m, out_data, out_nd, out_m, error, first_channel);
   
endmodule  