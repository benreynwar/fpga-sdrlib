// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module summult 
  #(
    parameter WDTH = 16,
    parameter MWDTH = 1,
    parameter N = 10
    )
   (
    input wire                clk,
    input wire                rst_n,
    input wire                in_nd,
    input wire [MWDTH-1:0]    in_m,
    input wire [2*WDTH*N-1:0] in_xs,
    input wire [WDTH*N-1:0]   in_ys,
    output wire [2*WDTH-1:0]  out_data,
    output reg                out_nd,
    output reg [MWDTH-1:0]    out_m,
    output reg                overflow
    );

   // When multiplying two signed numbers of width N the
   // required width of the result is 2N-1
   reg signed [2*WDTH-1:0]           out_data_re;
   reg signed [2*WDTH-1:0]           out_data_im;
   wire signed [2*WDTH-1:0]          shifted_re;
   wire signed [2*WDTH-1:0]          shifted_im;
   assign shifted_re = out_data_re >>> WDTH-1; 
   assign shifted_im = out_data_im >>> WDTH-1;
   assign out_data = {shifted_re[WDTH-1:0], shifted_im[WDTH-1:0]};

   {{inputassigns}}
   
   initial
     begin
        out_nd = 1'b0;
        overflow = 1'b0;
     end
   
   always @ (posedge clk)
     if (~rst_n)
       begin
        out_nd = 1'b0;
        overflow = 1'b0;
       end
     else
       begin
          if (in_nd)
            begin
               out_nd <= 1'b1;
               out_m <= in_m;
               //out_data_re <= in_xs[WDTH*(2*N-0)-1: WDTH*(2*N-1)] * in_ys[WDTH*N-1] + ...
               out_data_re <= {{real_sum}};
               //out_data_im <= in_xs[WDTH*(2*N-1)-1: WDTH*(2*N-2)] * in_ys[WDTH*N-1] + ...
               out_data_im <= {{imag_sum}};
               //$display("in_xs is %d", in_xs);
               //$display("in_xs is (%d %d) (%d %d) (%d %d) (%d %d)", in_x0_re, in_x0_im, in_x1_re, in_x1_im, in_x2_re, in_x2_im, in_x3_re, in_x3_im);
               //$display("in_ys is %d %d %d %d", in_y0, in_y1, in_y2, in_y3);
               //$display("in_xs is (%d %d) (%d %d) (%d %d)", in_x0_re, in_x0_im, in_x1_re, in_x1_im, in_x2_re, in_x2_im);
               //$display("in_ys is %d %d %d", in_y0, in_y1, in_y2);
               //$display("in_xs is (%d %d) (%d %d)", in_x0_re, in_x0_im, in_x1_re, in_x1_im);
               //$display("in_ys is %d %d", in_y0, in_y1);
               //$display("out data is %d %d", shifted_re, shifted_im);
               //$display("out data is %d", out_data);
            end
          else
            out_nd <= 1'b0;
       end
  
endmodule
