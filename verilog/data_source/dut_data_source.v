// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is simply a wrapper around the data_source module so that it can be accessed from the
// myhdl test bench.

module dut_data_source;
   reg                          clk;
   reg                          rst_n;
   wire [`WIDTH-1:0]            out_data;
   wire                         out_nd;
   wire [`MWIDTH-1:0]           out_m;
   wire                         error;
   
   initial begin
	  $from_myhdl(clk, rst_n);
	  $to_myhdl(out_data, out_nd, out_m, error);
   end
   
   data_source #(`SENDNTH, `LOGSENDNTH, `N_LOOPS, `LOGNLOOPS, `WIDTH, `MWIDTH, `N_DATA, `LOGNDATA) dut (clk, rst_n, out_nd, out_data, out_m, error);
   
endmodule  