// Answers are divided by 2.

module multiply_complex
  #(
    parameter WIDTH = 32
    )
   (
    input wire                     clk,
    input wire                     rst_n,
    input wire signed [WIDTH-1:0]  x,
    input wire signed [WIDTH-1:0]  y,
    output wire signed [WIDTH-1:0] z
    );

   wire signed [WIDTH/2-1:0]       x_re;
   wire signed [WIDTH/2-1:0]       x_im;
   wire signed [WIDTH/2-1:0]       y_re;
   wire signed [WIDTH/2-1:0]       y_im;
   assign x_re = x[WIDTH-1:WIDTH/2];
   assign x_im = x[WIDTH/2-1:0];
   assign y_re = y[WIDTH-1:WIDTH/2];
   assign y_im = y[WIDTH/2-1:0];
   
   wire signed [WIDTH/2-1:0]       xreyre;
   wire signed [WIDTH/2-1:0]       xreyim;
   wire signed [WIDTH/2-1:0]       ximyre;
   wire signed [WIDTH/2-1:0]       ximyim;

   wire signed [WIDTH/2:0]       z_re_l;
   wire signed [WIDTH/2:0]       z_im_l;
   wire signed [WIDTH/2-1:0]       z_re;
   wire signed [WIDTH/2-1:0]       z_im;

   assign z_re_l = xreyre - ximyim;
   assign z_im_l = xreyim + ximyre;
   assign z_re = z_re_l >> 1;
   assign z_im = z_im_l >> 1;
   assign z = {z_re, z_im};
   
   multiply #(WIDTH/2) multiply_0
     (.clk(clk),
      .rst_n(rst_n),
      .x(x_re),
      .y(y_re),
      .z(xreyre)
      );

   multiply #(WIDTH/2) multiply_1
     (.clk(clk),
      .rst_n(rst_n),
      .x(x_re),
      .y(y_im),
      .z(xreyim)
      );

   multiply #(WIDTH/2) multiply_2
     (.clk(clk),
      .rst_n(rst_n),
      .x(x_im),
      .y(y_re),
      .z(ximyre)
      );

   multiply #(WIDTH/2) multiply_3
     (.clk(clk),
      .rst_n(rst_n),
      .x(x_im),
      .y(y_im),
      .z(ximyim)
      );
   
endmodule


