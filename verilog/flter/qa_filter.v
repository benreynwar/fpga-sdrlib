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
    // Takes input messages to set taps.
    input wire [`MSG_WIDTH-1:0]  in_msg,
    input wire                   in_msg_nd, 
    output wire [WIDTH-1:0]      out_data,
    output wire                  out_nd,
    output wire [MWIDTH-1:0]      out_m,
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd,
    output wire                  error
    );

   filter #(WIDTH, 1, `FILTER_LENGTH, `FILTER_ID) filter_0
     (
      .clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .in_m(in_m),
      .in_msg(in_msg),
      .in_msg_nd(in_msg_nd),
      .out_data(out_data),
      .out_nd(out_nd),
      .out_m(out_m),
      .out_msg(out_msg),
      .out_msg_nd(out_msg_nd),
      .error(error)
      );

endmodule
