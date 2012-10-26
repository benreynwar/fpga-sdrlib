// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module qa_wrapper
  #(
    parameter WDTH = 32
    )
   (
    input wire                   clk,
    input wire                   rst_n,
    input wire [WDTH-1:0]        in_data,
    input wire                   in_nd,
    output wire [WDTH-1:0]        out_data,
    output wire                   out_nd
    );

   // Separate the input stream into a sample stream and a message stream.
   
   wire [WDTH-1:0]         in_samples;
   wire                    in_samples_nd;
   wire [`MSG_WIDTH-1:0]   in_msg;
   wire                    in_msg_nd;
   wire                    splitter_error;

   sample_msg_splitter #(WDTH) sample_msg_splitter_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .out_samples(in_samples),
      .out_samples_nd(in_samples_nd),
      .out_msg(in_msg),
      .out_msg_nd(in_msg_nd),
      .error(splitter_error)
      );

   // The qa module contains the actual blocks that we want to test.
   
   wire [WDTH-1:0]         out_samples;
   wire                    out_samples_nd;
   wire [`MSG_WIDTH-1:0]   out_msg;
   wire                    out_msg_nd;
   wire                    qa_error;
   wire [WDTH-1:0]         in_samples_shifted;
   assign in_samples_shifted = {in_samples[WDTH-3:WDTH/2-1], 1'b0, in_samples[WDTH/2-2: 0], 1'b0};
   
   qa_contents #(WDTH) qa_contents_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_samples_shifted),
      .in_nd(in_samples_nd),
      .in_msg(in_msg),
      .in_msg_nd(in_msg_nd),
      .out_data(out_samples),
      .out_nd(out_samples_nd),
      .out_msg(out_msg),
      .out_msg_nd(out_msg_nd),
      .error(error)
      );

   // The samples and messages are merged into common stream.
   
   wire                    combiner_error;
   wire [WDTH-1:0]         out_samples_shifted;
   assign out_samples_shifted = {2'b0, out_samples[WDTH-1 :WDTH/2+1], out_samples[WDTH/2-1 :1]};
        
   message_stream_combiner #(2, 1, WDTH) message_stream_combiner_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data({out_samples_shifted, out_msg}),
      .in_nd({out_samples_nd, out_msg_nd}),
      .out_data(out_data),
      .out_nd(out_nd),
      .error(combiner_error)
      );
        
endmodule