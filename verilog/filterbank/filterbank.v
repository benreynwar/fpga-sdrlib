// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module filterbank_ccf
  #(
    parameter N = 8,
    parameter LOG_N = 3,
    parameter WDTH = 32,
    parameter MWDTH = 1,
    parameter FLTLEN = 10,
    parameter LOG_FLTLEN = 4
    )
   (
    input wire                  clk,
    input wire                  rst_n,
    input wire [WDTH-1:0]       in_data,
    input wire                  in_nd,
    input wire [MWDTH-1:0]      in_m,
    // Takes input messages to set taps.
    input wire [`MSG_WIDTH-1:0] in_msg,
    input wire                  in_msg_nd, 
    
    output wire [WDTH-1:0]      out_data,
    output wire                 out_nd,
    output wire [MWDTH-1:0]     out_m,
    output wire                 first_filter,
    output wire                 error
    );
   
   reg [WDTH*(FLTLEN-1)-1:0]    histories[N-1:0];
   reg [LOG_N-1:0]              filter_n;
   reg [LOG_N-1:0]              filter_n_old;
   reg                          in_nd_old;
   reg [WDTH*(FLTLEN-1)-1:0]    shifted_history;
   wire [WDTH*(FLTLEN-1)-1:0]   mult_histories;
   wire                         in_first_filter;
   assign mult_histories = histories[filter_n];
   assign in_first_filter = (~|filter_n);

   // Tap values are set by the in_msg and in_msg_nd wires.
   // We assume that WDTH+1=MSG_WIDTH are the same.
   reg [LOG_N-1:0]              which_filter;
   reg [LOG_FLTLEN-1:0]         which_pos;
   reg                          setting_taps;
   reg [FLTLEN*WDTH/2-1:0]      tapvalues[N-1:0];
   wire signed [`MSG_WIDTH-1:0] signed_msg;
   wire signed [WDTH/2-1:0] small_signed_msg;

   wire                     summult_error;
   reg                     tap_set_error;
   assign error = summult_error | tap_set_error;

   assign signed_msg = in_msg;
   assign small_signed_msg = signed_msg;

   initial
     begin
        setting_taps <= 1'b0;
        tap_set_error <= 1'b0;
     end
   always @ (posedge clk)
     if (in_msg_nd)
       begin
          // If first bit is 1 then this is a header so we start reseting taps.
          if (in_msg[`MSG_WIDTH-1])
            begin
               which_filter <= {LOG_N{1'b0}};
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
               tapvalues[which_filter][(which_pos+1)*WDTH/2-1 -:WDTH/2] <= small_signed_msg;
               if (which_pos == FLTLEN-1)
                 begin
                    which_pos <= {LOG_FLTLEN{1'b0}};
                    if (which_filter == N-1)
                      setting_taps <= 1'b0;
                    else
                      which_filter <= which_filter + 1;
                 end
               else
                 which_pos <= which_pos + 1;
            end
       end
   
   genvar                     i;
   generate
      for (i=0; i<N; i=i+1) begin: loop_0
        initial
          histories[i] <= {WDTH*(FLTLEN-1){1'b0}};
      always @ (posedge clk)
        begin
           if (~rst_n)
             histories[i] <= {WDTH*(FLTLEN-1){1'b0}};
        end
      end
   endgenerate

   initial
     begin
        filter_n <= {LOG_N{1'b0}};
     end
   always @ (posedge clk)
     begin
        if (~rst_n)
          begin
             filter_n <= {LOG_N{1'b0}};
          end
        else
          begin
             in_nd_old <= in_nd;
             if (in_nd)
               begin
                  if (filter_n == N-1)
                    filter_n <= {LOG_N{1'b0}};
                  else
                    filter_n <= filter_n + 1;
                  shifted_history <= {histories[filter_n][WDTH*(FLTLEN-2)-1:0], in_data};
                  filter_n_old <= filter_n;
               end
             if (in_nd_old)
               begin
                  histories[filter_n_old] <= shifted_history;
               end
           end
     end

   summult #(WDTH/2, MWDTH+1, FLTLEN) summult_i
     (.clk(clk),
      .rst_n(rst_n),
      .in_nd(in_nd),
      .in_m({in_m, in_first_filter}),
      .in_xs({mult_histories, in_data}),
      .in_ys(tapvalues[filter_n]),
      .out_data(out_data),
      .out_nd(out_nd),
      .out_m({out_m, first_filter}),
      .overflow(summult_error)
      );

endmodule