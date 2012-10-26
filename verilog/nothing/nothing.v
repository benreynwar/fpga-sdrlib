// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module nothing
  #(
    parameter WDTH = 32,
    parameter MWDTH = 1
    )
   (
    input wire                   clk,
    input wire                   rst_n,
    input wire [WDTH-1:0]        in_data,
    input wire                   in_nd,
    input wire [MWDTH-1:0]       in_m,
    output reg [WDTH-1:0]        out_data,
    output reg                   out_nd,
    output reg [MWDTH-1:0]       out_m,
    `ifdef DEBUG
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd,
    `endif
    output reg                   error
    );

   `ifdef DEBUG

   reg [`MSG_WIDTH*2-1:0]        full_msg;
   reg                           full_msg_nd;
   wire                          msg_error;

   message_slicer #(2, `MSG_WIDTH, 8, 3) message_slicer_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(full_msg),
      .in_nd(full_msg_nd),
      .out_data(out_msg),
      .out_nd(out_msg_nd),
      .error(msg_error)
      );

   // Get shifted data.
   wire signed [WDTH/2-1:0]      in_data_re;
   assign in_data_re = in_data[WDTH-1:WDTH/2];
   wire signed [WDTH/2-1:0]      in_data_im;
   assign in_data_im = in_data[WDTH/2-1:0];
   wire signed [(`MSG_WIDTH-1)/2-1:0]   in_data_re_shifted;
   assign in_data_re_shifted = in_data_re >> `MSG_SHIFT;
   wire signed [(`MSG_WIDTH-1)/2-1:0]   in_data_im_shifted;
   assign in_data_im_shifted = in_data_im >> `MSG_SHIFT;
   wire [((`MSG_WIDTH-1)/2)*2-1:0]      in_data_shifted;
   assign in_data_shifted = {in_data_re_shifted, in_data_im_shifted};
   wire [`MSG_WIDTH-1:0]                in_data_msg;
   assign in_data_msg = in_data_shifted;
   
   initial
     begin
        full_msg_nd <= 1'b0;
     end

   always @ (posedge clk)
     begin
        error <= msg_error;
     end
   `endif

   initial
     error <= 1'b0;

   always @ (posedge clk)
     begin
   `ifdef DEBUG
        if (out_nd)
          begin
             full_msg_nd <= ~full_msg_nd;
             // format is {header, length excluding header, format code, module key, error key}
             // format code is always 0 for now.
             full_msg <= {1'b1, `MSG_LENGTH_WIDTH'd1, `MSG_FORMATCODE_WIDTH'd0, `MSG_MODULECODE_WIDTH'd0, `MSG_ERRORCODE_WIDTH'd0, in_data_msg};
          end
   `endif
        out_data <= in_data;
        out_m <= in_m;
        out_nd <= in_nd;
     end
   
endmodule