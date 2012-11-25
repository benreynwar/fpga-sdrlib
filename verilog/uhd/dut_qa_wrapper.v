// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is a wrapper around the nothing module so that it can be
// accessed from the myhdl test bench.

module dut_qa_wrapper;
   reg                   clk;
   reg                   reset;
   reg [`WIDTH-1:0]      in_data;
   reg                   in_nd;
   wire [`WIDTH-1:0]     out_data;
   wire                  out_nd;

   initial begin
	  $from_myhdl(clk, reset, in_data, in_nd);
      $to_myhdl(out_data, out_nd);
   end

   qa_wrapper #(`WIDTH) dut
     (clk, reset, in_data, in_nd, out_data, out_nd);
   
endmodule  