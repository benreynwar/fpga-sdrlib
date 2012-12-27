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
    output reg [WIDTH-1:0]       out_data,
    output reg                   out_nd,
    output reg [MWIDTH-1:0]      out_m,
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd, 
    output reg                   error
    );

   reg [WIDTH-1:0]               xa;
   reg [WIDTH-1:0]               xb;
   reg [WIDTH-1:0]               w;
   reg [2:0]                     counter;
   reg                           active;
   reg                           x_nd;
   reg [MWIDTH-1:0]              bf_in_m;
   wire [MWIDTH-1:0]             bf_out_m;
   
   always @ (posedge clk)
     begin
        // Default x_nd
        x_nd <= 1'b0;
        if (~rst_n)
          begin
             active <= 1'b0;
             counter <= 2'b0;
          end
        else if (in_nd)
          begin
             if (((~active)& (in_data != {WIDTH{1'b0}})) | (counter == 2'd0))
               begin
                  active <= 1'b1;
                  xa <= in_data;
                  counter <= 2'd1;
                  bf_in_m <= in_m;
               end
             else if (counter == 2'd1)
               begin
                  xb <= in_data;
                  counter <= 2'd2;
               end
             else if (counter == 2'd2)
               begin
                  w <= in_data;
                  counter <= 2'd0;
                  x_nd <= 1'b1;
               end
          end
     end

   wire [WIDTH-1:0] ya;
   wire [WIDTH-1:0] yb;
   reg [WIDTH-1:0]  yb_old;
   wire             y_nd;
   reg              y_nd_old;

   always @ (posedge clk)
     begin
        // default out_nd
        out_nd <= 1'b0;
        y_nd_old <= y_nd;
        error <= 1'b0;
        if (~rst_n)
          begin
             y_nd_old <= 1'b0;
          end
        else if (y_nd)
          begin
             if (y_nd_old)
               error <= 1'b1;
             yb_old <= yb;
             out_data <= ya;
             out_nd <= 1'b1;
             out_m <= bf_out_m;
          end
        else if (y_nd_old)
          begin
             out_data <= yb_old;
             out_nd <= 1'b1;
             out_m <= {MWIDTH{1'b0}};
          end
     end
   butterfly 
     #(.MWIDTH (MWIDTH),
	   .WIDTH (WIDTH)
	   )
   butterfly_0
     (.clk (clk),
	  .rst_n (rst_n),
	  .m_in (bf_in_m),
	  .w (w),
	  .xa (xa),
	  .xb (xb),
	  .x_nd (x_nd),
	  .m_out (bf_out_m),
	  .ya (ya),
	  .yb (yb),
	  .y_nd (y_nd)
	  );
   

  endmodule