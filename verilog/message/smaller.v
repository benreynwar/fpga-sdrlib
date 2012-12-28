// -*- verilog -*-
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module smaller #(parameter WIDTH = 32)
   (input wire [WIDTH-1:0] in_val,
    output wire [WIDTH-1:0] out_val
    );
   wire signed [WIDTH/2-1:0] val_re;
   wire signed [WIDTH/2-1:0] val_im;
   wire signed [WIDTH/2-2:0] val_re_s;
   wire signed [WIDTH/2-2:0] val_im_s;
   assign val_re = in_val[WIDTH-1:WIDTH/2];
   assign val_im = in_val[WIDTH/2-1:0];
   assign val_re_s = val_re >> 1;
   assign val_im_s = val_im >> 1;
   assign out_val = {2'b0, val_re_s, val_im_s};
endmodule

