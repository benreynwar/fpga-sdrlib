// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module nothing
  #(
    parameter WDTH = 32,
    parameter MWDTH = 1
    )
   (
    input wire             clk,
    input wire             rst_n,
    input wire [WDTH-1:0]  in_data,
    input wire             in_nd,
    input wire [MWDTH-1:0] in_m, 
    output reg [WDTH-1:0]  out_data,
    output reg             out_nd,
    output reg [MWDTH-1:0] out_m,
    `ifdef DEBUG
    output reg             error,
    output wire [WDTH-1:0] msg,
    output wire            msg_nd
    `else
    output reg             error
    `endif
    );

   `ifdef DEBUG

   reg [WDTH*2-1:0]        full_msg;
   reg                     full_msg_nd;
   wire                    msg_error;

   message_slicer #(2, WDTH, 8, 3) message_slicer_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(full_msg),
      .in_nd(full_msg_nd),
      .out_data(msg),
      .out_nd(msg_nd),
      .error(msg_error)
      );
   
   initial
     begin
        full_msg_nd <= 1'b0;
     end

   always @ (posedge clk)
     begin
        if (msg_nd)
          //$display("Message out is %d", msg);
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
             full_msg <= {1'b0, 10'd1, 4'd0, 10'd0, 7'd0, in_data};
          end
   `endif
        out_data <= in_data;
        out_m <= in_m;
        out_nd <= in_nd;
     end
   
endmodule