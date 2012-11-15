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

   wire [WDTH-1:0]         before_data;
   wire [WDTH-1:0]         after_data;
   wire [WDTH-1:0]         before_samples_shifted;
   wire [WDTH-1:0]         after_samples_shifted;
   wire                    before_nd;
   wire                    after_nd;
   wire [`MSG_WIDTH-1:0]   before_msg;
   wire                    before_msg_nd;
   wire [`MSG_WIDTH-1:0]   after_msg;
   wire                    after_msg_nd;
   wire                    splitter_error;
   
   wire                    rst_n;
   assign rst_n = ~reset;

   sample_msg_splitter #(WDTH) sample_msg_splitter_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .out_samples(before_data),
      .out_samples_nd(before_nd),
      .out_msg(before_msg),
      .out_msg_nd(before_msg_nd),
      .error(splitter_error)
      );

   assign after_nd = before_nd;
   assign after_msg_nd = before_msg_nd;
   assign after_msg = before_msg;
   assign before_samples_shifted = {before_data[WDTH-3:WDTH/2-1], 1'b0, before_data[WDTH/2-2: 0], 1'b0};
   assign after_data = before_samples_shifted; 
  assign after_samples_shifted = {2'b0, after_data[WDTH-1 :WDTH/2+1], after_data[WDTH/2-1 :1]};
   
   message_stream_combiner #(2, 1, WDTH) message_stream_combiner_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data({after_samples_shifted, after_msg}),
      .in_nd({after_nd, after_msg_nd}),
      .out_data(out_data),
      .out_nd(out_nd),
      .error(combiner_error)
      );

endmodule