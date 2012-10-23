// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is a wrapper around the nothing module so that it can be
// accessed from the myhdl test bench.

module dut_nothing;
   reg                   clk;
   reg                   rst_n;
   reg [`WIDTH-1:0]       in_data;
   reg                   in_nd;
   reg [`MWIDTH-1:0]      in_m;
   wire [`WIDTH-1:0]      out_data;
   wire                  out_nd;
   wire [`MWIDTH-1:0]     out_m;
   wire                  error;
   `ifdef DEBUG
   wire [`WIDTH-1:0]      msg;
   wire                  msg_nd;
   `endif

   initial begin
	  $from_myhdl(clk, rst_n, in_data, in_nd, in_m);
   `ifdef DEBUG
      $to_myhdl(out_data, out_nd, out_m, error, msg, msg_nd);
   `else
	  $to_myhdl(out_data, out_nd, out_m, error);
      `endif
   end

   `ifdef DEBUG
   nothing #(`WIDTH, `MWIDTH) dut
     (clk, rst_n, in_data, in_nd, in_m, out_data, out_nd, out_m, error, msg, msg_nd);
   `else
   nothing #(`WIDTH, `MWIDTH) dut
     (clk, rst_n, in_data, in_nd, in_m, out_data, out_nd, out_m, error);
   `endif
   
endmodule  