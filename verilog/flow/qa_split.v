// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// A qa_wrapper with a splitter.  Only the first stream is returned.

module qa_wrapper
  #(
    parameter WDTH = 32
    )
   (
    input wire             clk,
    input wire             reset,
    input wire [WDTH-1:0]  in_data,
    input wire             in_nd,
    output wire [WDTH-1:0] out_data,
    output wire            out_nd
    );

   // Separate the input stream into a sample stream and a message stream.

   wire [WDTH-1:0]         null_data;
   
   wire                    rst_n;
   assign rst_n = ~reset;

   split #(2, 1) split_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .out_data({null_data, out_data}),
      .out_nd(out_nd)
      );
   
endmodule