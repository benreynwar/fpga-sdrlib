// -*- verilog -*-
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// Testing sending back debug messages.

module qa_contents
  #(
    parameter WIDTH = 32,
    parameter MWIDTH = 1
    )
   (
    input wire                   clk,
    input wire                   rst_n,
    input wire [WIDTH-1:0]       in_data,
    input wire                   in_nd,
    input wire [MWIDTH-1:0]      in_m,
    input wire [`MSG_WIDTH-1:0]  in_msg,
    input wire                   in_msg_nd, 
    output wire [WIDTH-1:0]      out_data,
    output wire                  out_nd,
    output wire [MWIDTH-1:0]     out_m,
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd, 
    output wire                  error
    );

   localparam integer MSGLENGTH = 2;
   reg [MSGLENGTH*WIDTH-1:0] msg;
   reg                       msg_nd;
   wire [WIDTH-1:0]          small_data;
   smaller #(WIDTH) smaller_0 (in_data, small_data);

   assign out_nd = in_nd;
   assign out_m = in_m;
   assign out_data = in_data;
   
   always @ (posedge clk)
     begin
        msg_nd <= 1'b0;
        if (~rst_n)
          begin
          end
        else if (in_nd)
          begin
             // If divisible by four send an error message.
             // Not if it is 0.
             if ((in_data[1:0] == 2'b0) & (|in_data))
               begin
                  msg <= {1'b1, 10'd1, 21'd0, small_data};
                  msg_nd <= 1'b1;
               end
          end
     end

   message_slicer #(MSGLENGTH, WIDTH, 48) message_slicer_0
     (clk, rst_n, msg, msg_nd, out_msg, out_msg_nd, error);

  endmodule