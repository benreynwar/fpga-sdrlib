// -*- verilog -*-
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

/*
 Implements a butterfly module for a FFT.
 
 Takes complex numbers W, XA, XB and returns
 YA = XA + W*XB
 YB = XA - W*XB
 
 It can take input no more frequently than once every
 two steps.  This is so, hopefully, less multiply
 blocks can be used.
 */

{% if not xilinx %}

module MULT18X18S
  (output reg signed [35:0] P,
   input signed [17:0] A,
   input signed [17:0] B,
   input C,    // Clock
   input CE,   // Clock Enable
   input R     // Synchronous Reset
   );
   
   always @(posedge C)
     if(R)
       P <= 36'sd0;
     else if(CE)
       P <= A * B;

endmodule // MULT18X18S

{% endif %}

module multiply
  #(
    parameter WDTH = 0
    )
   (
    input wire                   clk,
    input wire                   rst_n,
    input wire signed [WDTH-1:0] x,
    input wire signed [WDTH-1:0] y,
    output reg signed [WDTH-1:0] z
    );

   reg                          ce;
   initial
     ce <= 1'b1;
   
   wire signed [17:0]            xb;
   wire signed [17:0]            yb;
   assign xb = x;
   assign yb = y;
   wire signed [35:0]       xy;
   
   MULT18X18S multer (.P(xy), .A(xb), .B(yb), .C(clk), .CE(ce), .R(~rst_n));   


   always @ (posedge clk)
     begin
        //xy <= xb * yb;
        z <= xy >>> (WDTH-2);
      end
   
endmodule


module butterfly
  #(
    // The width of m_in.
    parameter M_WDTH = 0,
    // The width of the input, output and twiddle factors.
    parameter X_WDTH = 0
    )
   (
    input wire                        clk,
    input wire                        rst_n,
    // m_in contains data that passes through this block with no change.
    // It is delayed for 3 counts like x_nd->y_nd.
    input wire [M_WDTH-1:0]           m_in,
    // The twiddle factor.
    input wire signed [2*X_WDTH-1:0]  w,
    // XA
    input wire signed [2*X_WDTH-1:0]  xa,
    // XB
    input wire signed [2*X_WDTH-1:0]  xb,
    // Set to 1 when new data is present on inputs.
    // Cannot be set to 1 for two consecutive steps.
    input wire                        x_nd,
    // delayed version of m_in.
    output reg [M_WDTH-1:0]           m_out,
    // YA = XA + W*XB
    // YB = XA - W*XB
    // When y_nd=1 y_re and y_im are outputing YA.
    // The step after they are outputting YB.
    output wire signed [2*X_WDTH-1:0] y,
    output reg                        y_nd
    );

   // Set wire to the real and imag parts for convenience.
   wire signed [X_WDTH-1:0]        w_re;
   wire signed [X_WDTH-1:0]        w_im;
   assign w_re = w[2*X_WDTH-1:X_WDTH];
   assign w_im = w[X_WDTH-1:0];
   wire signed [X_WDTH-1:0]        xa_re;
   wire signed [X_WDTH-1:0]        xa_im;
   assign xa_re = xa[2*X_WDTH-1:X_WDTH];
   assign xa_im = xa[X_WDTH-1:0];
   wire signed [X_WDTH-1:0]        xb_re;
   wire signed [X_WDTH-1:0]        xb_im;
   assign xb_re = xb[2*X_WDTH-1:X_WDTH];
   assign xb_im = xb[X_WDTH-1:0];
   reg signed [X_WDTH-1: 0]        y_re;
   reg signed [X_WDTH-1: 0]        y_im;
   assign y = {y_re, y_im};
   
   // Delayed m_in.
   reg signed [M_WDTH-1:0]         m[3:0];
   // Delayed XA
   reg signed [X_WDTH-1:0]         za_re[2:0];
   reg signed [X_WDTH-1:0]         za_im[2:0];
   // Delayed XB
   reg signed [X_WDTH-1:0]         zb_re;
   reg signed [X_WDTH-1:0]         zb_im;
   // Delayed W
   reg signed [X_WDTH-1:0]         ww_re;
   reg signed [X_WDTH-1:0]         ww_im;
   // Delayed x_nd
   reg signed                      x_nd_old[4:0];
   // Output of multipliers
   wire signed [X_WDTH-1:0]         xbrewre;
   wire signed [X_WDTH-1:0]         xbimwim;
   wire signed [X_WDTH-1:0]         xbrewim;
   wire signed [X_WDTH-1:0]         xbimwre;
   // W * XB
   reg signed [X_WDTH-1:0]         zbw_re;
   reg signed [X_WDTH-1:0]         zbw_re_old;
   wire signed [X_WDTH-1:0]        zbw_im;
   assign zbw_im = xbrewim + xbimwre;
   reg signed [X_WDTH-1:0]         zbw_im_old;
   // Wire of longer length for adding or substracting W*XB to XA.
   // If we don't create longer wires for them then we can lose the
   // high bit.  The contents of these wires are downshifted into a
   // normal size for use.
   wire signed [X_WDTH:0]            z1_re_big;
   wire signed [X_WDTH:0]            z1_im_big;
   assign z1_re_big = za_re[1] + zbw_re;
   assign z1_im_big = za_im[1] + zbw_im;
   wire signed [X_WDTH:0]            z2_re_big;
   wire signed [X_WDTH:0]            z2_im_big;
   assign z2_re_big = za_re[2] - zbw_re_old;
   assign z2_im_big = za_im[2] - zbw_im_old;
   
   // Create four multiply modules.
   multiply #(X_WDTH) multiply_0
     (.clk(clk),
      .rst_n(rst_n),
      .x(xb_re),
      .y(w_re),
      .z(xbrewre)
      );
   multiply #(X_WDTH) multiply_1
     (.clk(clk),
      .rst_n(rst_n),
      .x(xb_im),
      .y(w_im),
      .z(xbimwim)
      );
   multiply #(X_WDTH) multiply_2
     (.clk(clk),
      .rst_n(rst_n),
      .x(zb_re),
      .y(ww_im),
      .z(xbrewim)
      );
   multiply #(X_WDTH) multiply_3
     (.clk(clk),
      .rst_n(rst_n),
      .x(zb_im),
      .y(ww_re),
      .z(xbimwre)
      );
   
  always @ (posedge clk)
    begin
      if (!rst_n)
        begin
           y_nd <= 1'b0;
        end
      else
        begin
           // Set delay for x_nd_old and m.
           x_nd_old[0] <= x_nd;
           x_nd_old[1] <= x_nd_old[0];
           x_nd_old[2] <= x_nd_old[1];
           x_nd_old[3] <= x_nd_old[2];
           x_nd_old[4] <= x_nd_old[3];
           m[0] <= m_in;
           m[1] <= m[0];
           m[2] <= m[1];
           m[3] <= m[2];
           m_out <= m[3];
           // STAGE 1
           if (x_nd)
             begin
                za_re[0] <= xa_re;
                za_im[0] <= xa_im;
                ww_re <= w_re;
                ww_im <= w_im;
                zb_re <= xb_re;
                zb_im <= xb_im;
                // Multiplications for calculate the real part
                // of W*XB are occuring.
                if (x_nd_old[0])
                  $display("ERROR: BF got new data two steps in a row.");
             end // if (x_nd)
           // STAGE 2
           // STAGE 2 is empty. Hopefully this gives multiplication more time.
           // STAGE 3
           if (x_nd_old[1])
             begin
                za_re[1] <= za_re[0];
                za_im[1] <= za_im[0];
                // Downshift the multiplied results into normal width and
                // substract them.
                // Overflow is not possible upon subtraction since we
                // know that W and XB both have magnitude less than 1
                // so their multiple must also.
                zbw_re <= xbrewre - xbimwim;
                // Multiplications for the imag part of W*XB start here.
             end
           // STAGE 3
           // STAGE 3 is empty. Hopefully this gives multiplication more time.
           // STAGE 4
           if (x_nd_old[3])
             begin
                // We only need to shift the required delayed data
                // with XA every two steps since new input cannot
                // arrive more frequently than that.
                // XA is needed by a wire calculating z2_re_big and ze_im_big
                // next step.
                za_re[2] <= za_re[1];
                za_im[2] <= za_im[1];
                // Output YA.
                y_nd <= 1'b1;
                y_re <= z1_re_big >>> 1;
                y_im <= z1_im_big >>> 1;
                zbw_im_old <= zbw_im;
                zbw_re_old <= zbw_re;
             end
           // STAGE 4
           if (x_nd_old[4])
             begin
                // Output YB.
                y_nd <= 1'b0;
                y_re <= z2_re_big >>> 1;
                y_im <= z2_im_big >>> 1;
             end
        end
    end

endmodule