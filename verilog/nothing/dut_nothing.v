// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is a wrapper around the nothing module so that it can be
// accessed from the myhdl test bench.

module dut_nothing;
   reg                   clk;
   reg                   rst_n;
   reg [`WIDTH-1:0]      in_data;
   reg                   in_nd;
   reg [`MWIDTH-1:0]     in_m;
   reg [`MSG_WIDTH-1:0]  in_msg;
   reg                   in_msg_nd;
   wire [`WIDTH-1:0]     out_data;
   wire                  out_nd;
   wire [`MWIDTH-1:0]    out_m;
   wire [`MSG_WIDTH-1:0] out_msg;
   wire                  out_msg_nd;
   wire                  error;

   initial begin
	  $from_myhdl(clk, rst_n, in_data, in_nd, in_m, in_msg, in_msg_nd);
      $to_myhdl(out_data, out_nd, out_m, out_msg, out_msg_nd, error);
   end

   `ifdef DEBUG
   nothing #(`WIDTH, `MWIDTH) dut
     (clk, rst_n, in_data, in_nd, in_m, out_data, out_nd, out_m, out_msg, out_msg_nd, error);
   `else
   nothing #(`WIDTH, `MWIDTH) dut
     (clk, rst_n, in_data, in_nd, in_m, out_data, out_nd, out_m, error);
   `endif
   
endmodule  