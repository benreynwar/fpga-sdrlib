// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is a wrapper around a module so that it can be
// accessed from the myhdl test bench.

module dut_filterbank_ccf;
   reg                   clk;
   reg                   rst_n;
   reg [`WIDTH-1:0]       in_data;
   reg                   in_nd;
   reg [`MWIDTH-1:0]      in_m;
   reg                   in_msg_nd;
   reg [`MSG_WIDTH-1:0]  in_msg;
   wire [`WIDTH-1:0]      out_data;
   wire                  out_nd;
   wire [`MWIDTH-1:0]     out_m;
   wire                  first_filter;
   wire                  error;
   
   initial begin
	  $from_myhdl(clk, rst_n, in_data, in_nd, in_m, in_msg_nd, in_msg);
	  $to_myhdl(out_data, out_nd, out_m, first_filter, error);
   end

   filterbank_ccf #(`N, `LOG_N, `WIDTH, `MWIDTH, `FLTLEN, `LOG_FLTLEN) dut
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .in_m(in_m),
      .in_msg_nd(in_msg_nd),
      .in_msg(in_msg),
      .out_data(out_data),
      .out_nd(out_nd),
      .out_m(out_m),
      .first_filter(first_filter),
      .error(error)
      );

endmodule  