// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module qa_contents
  #(
    parameter WDTH = 32
    )
   (
    input wire                   clk,
    input wire                   rst_n,
    input wire [WDTH-1:0]        in_data,
    input wire                   in_nd,
    input wire [`MSG_WIDTH-1:0]  in_msg,
    input wire                   in_msg_nd,
    output wire [WDTH-1:0]       out_data,
    output wire                  out_nd,
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd,
    output wire                  error
    );

   nothing #(WDTH, 1) nothing_0
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .in_m(in_m),
      .out_data(out_data),
      .out_nd(out_nd),
      .out_m(out_m),
`ifdef DEBUG
      .out_msg(out_msg),
      .out_msg_nd(out_msg_nd),
`endif
      .error(error)
      );
   
endmodule