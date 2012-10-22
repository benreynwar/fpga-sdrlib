// -*- verilog -*-
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is a qa module to put on an FPGA for testing.

module qa
  (
   input wire               clk,
   input wire               reset,
   output wire [{{width}}-1:0] out_data,
   output wire              out_nd
   );
   
   wire                     out_error;
   wire [{{mwidth}}-1:0]       out_m;
   wire                        rst_n;

   assign rst_n = ~reset;
   
   data_source #({{sendnth}}, {{logsendnth}}, {{width}}, {{mwidth}}, {{n_data}}, {{logndata}}) dut (clk, rst_n, out_nd, out_data, out_m, out_error);
   
endmodule  