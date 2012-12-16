// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// A qa_wrapper with a splitter and message_stream_combiner

module qa_wrapper
  #(
    parameter WDTH = 32
    )
   (
    input wire            clk,
    input wire            reset,
    input wire [WDTH-1:0] in_data,
    input wire            in_nd,
    output reg [WDTH-1:0] out_data,
    output reg            out_nd
    );

   // Separate the input stream into a sample stream and a message stream.

   wire [WDTH-1:0]         mid1_data;
   wire [WDTH-1:0]         mid2_data;
   wire [WDTH-1:0]         staged_data;
   wire                    staged_nd;
   wire                    mid_nd;
   wire                    splitter_error;
   
   wire                    rst_n;
   assign rst_n = ~reset;

   split #(2, 1) split_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .out_data({mid1_data, mid2_data}),
      .out_nd(mid_nd)
      );
   
   message_stream_combiner
     #(2, 1, WDTH, `COMBINER_BUFFER_LENGTH, `LOG_COMBINER_BUFFER_LENGTH,
       `MAX_PACKET_LENGTH, `MSG_LENGTH_WIDTH)
   message_stream_combiner_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data({mid1_data, mid2_data}),
      .in_nd({mid_nd, mid_nd}),
      .out_data(staged_data),
      .out_nd(staged_nd),
      .error(combiner_error)
      );

   always @ (posedge clk)
     begin
        if (combiner_error)
          begin
             out_nd <= 1'b1;
             out_data <= `ERRORCODE;
          end
        else
          begin
             out_nd <= staged_nd;
             out_data <= staged_data;
          end
     end

endmodule