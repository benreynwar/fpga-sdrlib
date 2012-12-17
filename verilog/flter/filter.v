// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module filter
  #(
    parameter WIDTH = 32,
    parameter MWIDTH = 1,
    parameter FLTLEN = 10,
    // ID is used to work out whether messages are
    // directed to it.
    parameter ID = 0
    )
   (
    input wire                  clk,
    input wire                  rst_n,
    input wire [WIDTH-1:0]      in_data,
    input wire                  in_nd,
    input wire [MWIDTH-1:0]     in_m,
    // Takes input messages to set taps.
    input wire [`MSG_WIDTH-1:0] in_msg,
    input wire                  in_msg_nd, 
    output wire [WIDTH-1:0]     out_data,
    output wire                 out_nd,
    output wire [MWIDTH-1:0]    out_m,
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd, 
    output wire                 error
    );

   localparam integer LOG_FLTLEN = $ceil($log10(FLTLEN)/$log10(2));
     
   reg [WIDTH*(FLTLEN-1)-1:0]   history;
   reg                          in_nd_old;
   reg [WIDTH*(FLTLEN-1)-1:0]   shifted_history;
   wire                         in_first_filter;
   
   // Tap values are set by the in_msg and in_msg_nd wires.
   // We assume that WIDTH+1=MSG_WIDTH are the same.
   reg [LOG_FLTLEN-1:0]         which_pos;
   reg                          setting_taps;
   reg [FLTLEN*WIDTH/2-1:0]     tapvalues;
   wire signed [`MSG_WIDTH-1:0] signed_msg;
   wire signed [WIDTH/2-1:0]    small_signed_msg;
   
   wire                         summult_error;
   reg                          tap_set_error;
   assign error = summult_error | tap_set_error;
   
   assign signed_msg = in_msg;
   assign small_signed_msg = signed_msg;

   always @ (posedge clk)
     if (!rst_n)
       begin
          setting_taps <= 1'b0;
          tap_set_error <= 1'b0;
       end
     else if (in_msg_nd)
       begin
          // If first bit is 1 then this is a header so we start reseting taps.
          if (in_msg[`MSG_WIDTH-1])
            begin
               which_pos <= {LOG_FLTLEN{1'b0}};
               setting_taps <= 1'b1;
               // We tried to set taps while being in the middle of setting them.
               if (setting_taps)
                 begin
                    tap_set_error <= 1'b1;
                 end
            end
          else if (setting_taps)
            begin
               tapvalues[(which_pos+1)*WIDTH/2-1 -:WIDTH/2] <= small_signed_msg;
               if (which_pos == FLTLEN-1)
                 begin
                    which_pos <= {LOG_FLTLEN{1'b0}};
                    setting_taps <= 1'b0;
                 end
               else
                 which_pos <= which_pos + 1;
            end
       end
   
   always @ (posedge clk)
     begin
        if (~rst_n)
          begin
             history <= {WIDTH*(FLTLEN-1){1'b0}};
          end
        else
          begin
             in_nd_old <= in_nd;
             if (in_nd)
               begin
                  shifted_history <= {history[WIDTH*(FLTLEN-2)-1:0], in_data};
               end
             if (in_nd_old)
               begin
                  history <= shifted_history;
               end
           end
     end

   summult #(WIDTH/2, MWIDTH, FLTLEN) summult_i
     (.clk(clk),
      .rst_n(rst_n),
      .in_nd(in_nd),
      .in_m({in_m}),
      .in_xs({history, in_data}),
      .in_ys(tapvalues),
      .out_data(out_data),
      .out_nd(out_nd),
      .out_m({out_m}),
      .overflow(summult_error)
      );

endmodule