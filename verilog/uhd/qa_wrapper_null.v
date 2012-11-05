// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This qa_wrapper simple connect transmit to receive.

module qa_wrapper
  #(
    parameter WDTH = 32
    )
   (
    input wire                   clk,
    input wire                   reset,
    input wire [WDTH-1:0]        in_data,
    input wire                   in_nd,
    output wire [WDTH-1:0]        out_data,
    output wire                   out_nd
    );

   assign out_data = in_data;
   assign out_nd = in_nd;
        
endmodule