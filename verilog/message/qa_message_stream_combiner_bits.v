// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// A qa_wrapper with only the message_stream_combiner.
// The input stream and an empty stream go to the combiner.

module qa_wrapper
  #(
    parameter WIDTH = 32
    )
   (
    input wire             clk,
    input wire             reset,
    input wire [WIDTH-1:0]  in_data,
    input wire             in_nd,
    output wire [WIDTH-1:0] out_data,
    output wire            out_nd
    );

   reg                     empty_nd;
   reg [WIDTH-1:0]         empty_data;
   wire                     mid_nd;
   wire [WIDTH-1:0]         mid_data;
   wire                    combiner_error;
   wire                    bits_error;
   
   always @ (posedge clk)
     if (reset)
       begin
          empty_nd <= 1'b0;
          empty_data <= 12;
       end
   
   assign rst_n = ~reset;

   message_stream_combiner #(2, 1, WIDTH, `COMBINER_BUFFER_LENGTH, `LOG_COMBINER_BUFFER_LENGTH, `MAX_PACKET_LENGTH, `MSG_LENGTH_WIDTH) message_stream_combiner_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data({in_data, empty_data}),
      .in_nd({in_nd, empty_nd}),
      .out_data(mid_data),
      .out_nd(mid_nd),
      .error(combiner_error)
      );

   bits #(WIDTH) bits_0
     (.clk(clk),
      .reset(reset),
      .in_data(mid_data),
      .in_nd(mid_nd),
      .out_data(out_data),
      .out_nd(out_nd),
      .error(bits_error)
      );

endmodule