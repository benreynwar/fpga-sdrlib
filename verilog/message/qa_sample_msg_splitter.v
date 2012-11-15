// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// A qa_wrapper with only the sample_msg_splitter module to test.

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
   
   wire [`MSG_WIDTH-1:0]   out_msg;
   wire                    out_msg_nd;
   wire                    splitter_error;
   
   wire                    rst_n;
   assign rst_n = ~reset;

   sample_msg_splitter #(WDTH) sample_msg_splitter_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .out_samples(out_data),
      .out_samples_nd(out_nd),
      .out_msg(out_msg),
      .out_msg_nd(out_msg_nd),
      .error(splitter_error)
      );

endmodule