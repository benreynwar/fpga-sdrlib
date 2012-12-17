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

   wire signed [WDTH-1:0]     x_re_y [N-1:0];
   wire signed [WDTH-1:0]     x_im_y [N-1:0];
   // When multiplying two signed numbers of width N the
   // required width of the result is 2N-1
   reg signed [WDTH-1:0]      out_data_re;
   reg signed [WDTH-1:0]      out_data_im;
   reg [1:0]                  p_nd;
   reg [MWDTH-1:0]            p_m[1:0];           
   assign out_data = {out_data_re, out_data_im};
   
   initial
     begin
        p_nd <= 2'b0;
        out_nd <= 1'b0;
        overflow <= 1'b0;
     end
   genvar i;
   generate
      for (i=0; i<N; i=i+1) begin: loop_0
         wire signed [WDTH-1:0]     x_re;
         wire signed [WDTH-1:0]     x_im;
         wire signed [WDTH-1:0]     y;
    
         assign x_re = in_xs[WDTH*(2*(i+1))-1 -:WDTH];
         assign x_im = in_xs[WDTH*(2*(i+1)-1)-1 -:WDTH];
         assign y = in_ys[WDTH*(i+1)-1 -:WDTH];

         multiply #(WDTH) mult_inst0 (clk, rst_n, x_re, y, x_re_y[i]);
         multiply #(WDTH) mult_inst1 (clk, rst_n, x_im, y, x_im_y[i]);

      end
   endgenerate

   always @ (posedge clk)
     if (~rst_n)
       begin
          p_nd <= 2'b0;
          out_nd <= 1'b0;
          overflow <= 1'b0;
       end
     else
       begin
          p_nd[0] <= in_nd;
          p_nd[1] <= p_nd[0];
          out_nd <= p_nd[1];
          p_m[0] <= in_m;
          p_m[1] <= p_m[0];
          out_m <= p_m[1];
          // The output should be ready from the multiplier.
          if (p_nd[1])
            begin
               //out_data_re <= x_re_y[0] + x_re_y[1] + ...
               out_data_re <= {{real_sum}};
               //out_data_re <= x_im_y[0] + x_im_y[1] + ...
               out_data_im <= {{imag_sum}};
            end
       end
  
endmodule
