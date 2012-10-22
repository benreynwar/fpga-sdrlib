// -*- verilog -*-
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is a wrapper around the nothing module so that it can be
// incorporated into an FPGA.

module qa
  (
   input wire                  clk,
   input wire                  reset,
   input wire [{{width}}-1:0]  in_data,
   input wire                  in_nd,
   output wire [{{width}}-1:0] out_data,
   output wire                 out_nd
   );
   
   wire                        first;
   wire                        error;
   wire [{{mwidth}}-1:0]       in_m;
   wire [{{mwidth}}-1:0]       out_m;   
   wire                        rst_n;
   
   assign rst_n = ~reset;

   dit
     #({{n}},{{logn}},{{width}},{{width}},{{mwidth}})
   dut
     (clk, rst_n,
      in_data, in_nd, in_m,
      out_data, out_nd, out_m,
      first, error);
   
endmodule  