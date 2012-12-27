// -*- verilog -*-
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

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
    output reg                   out_nd,
    output reg [MWIDTH-1:0]      out_m,
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd, 
    output reg                   error
    );

   reg [WIDTH-1:0]               x;
   reg                           counter;
   reg                           active;

   always @ (posedge clk)
     begin
        out_nd <= 1'b0;
        if (~rst_n)
          begin
             active <= 1'b0;
             counter <= 1'b0;
             error <= 1'b0;
          end
        else if (in_nd)
          begin
             if (((~active)& (in_data != {WIDTH{1'b0}})) | (counter == 1'd0))
               begin
                  active <= 1'b1;
                  x <= in_data;
                  counter <= 1'b1;
               end
             else if (counter == 1'b1)
               begin
                  counter <= 1'b0;
                  out_nd <= 1'b1;
               end
          end
     end

   multiply_complex #(WIDTH) multiply_complex_0
     (.clk(clk),
      .rst_n(rst_n),
      .x(x),
      .y(in_data),
      .z(out_data)
      );

  endmodule