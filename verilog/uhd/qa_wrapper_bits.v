// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This qa_wrapper takes the data and outputs alternately
// bit position and bit contents.
// If data arrives too frequently then ERRORCODE is output.

module qa_wrapper
  #(
    parameter WIDTH = 32
    )
   (
    input wire              clk,
    input wire              reset,
    input wire [WIDTH-1:0]  in_data,
    input wire              in_nd,
    output wire [WIDTH-1:0] out_data,
    output wire             out_nd
    );

   wire                    error;

   bits #(WIDTH) bits_0
     (.clk(clk),
      .reset(reset),
      .in_data(in_data),
      .in_nd(in_nd),
      .out_data(out_data),
      .out_nd(out_nd),
      .error(error)
      );
                         
endmodule