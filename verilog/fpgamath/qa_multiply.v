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

   wire [WIDTH/2-1:0]             x;
   wire [WIDTH/2-1:0]             y;
   wire [WIDTH/2-1:0]             z;
   assign x = in_data[WIDTH-1:WIDTH/2];
   assign y = in_data[WIDTH/2-1:0];
   assign out_data = {{WIDTH/2{1'b0}}, z};

   always @ (posedge clk)
     if (~rst_n)
       error <= 1'b0;
     else
       begin
          out_nd <= in_nd;
       end
   
   multiply #(WIDTH/2) multiply_0
     (.clk(clk),
      .rst_n(rst_n),
      .x(x),
      .y(y),
      .z(z)
      );

  endmodule