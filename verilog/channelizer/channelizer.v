// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module channelizer
  #(
    parameter N = 8,
    parameter LOGN = 3,
    parameter WDTH = 32,
    parameter MWDTH = 1,
    parameter FLTLEN = 10
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
    output wire            error,
    output reg             first_channel
    );
   
   wire                   filtered_nd;
   wire [WDTH-1:0]        filtered_data;
   wire [MWDTH-1:0]       filtered_m;
   wire                   filtered_error;
   wire                   filtered_ff;

   assign error = (filtered_error | channelized_error | unaligned);

   always @ (posedge clk or negedge rst_n)
     begin
        if (rst_n)
          begin
//             $display("error is %d", error);
             if (filtered_error)
               $display("FILTERED_ERROR");
             if (channelized_error)
               $display("CHANNELIZED_ERROR");
             if (unaligned)
               $display("UNALIGNED");             
          end
     end

   filterbank_ccf #(N, LOGN, WDTH, MWDTH, FLTLEN) filterbank_ccf_i
     (.clk(clk),
      .rst_n(rst_n),
      .in_data(in_data),
      .in_nd(in_nd),
      .in_m(in_m),
      .out_data(filtered_data),
      .out_nd(filtered_nd),
      .out_m(filtered_m),
      .first_filter(filtered_ff),
      .error(filtered_error)
      );

   wire [WDTH-1:0]        channelized_data;
   wire                   channelized_nd;
   wire [MWDTH-1:0]       channelized_m;
   wire                   channelized_ff;
   wire                   channelized_first;
   wire                   channelized_error;

   dit #(N, LOGN, WDTH/2, WDTH/2, MWDTH+1) dit_i
       (.clk(clk),
        .rst_n(rst_n),
        .in_x(filtered_data),
        .in_nd(filtered_nd),
        .in_w({filtered_m, filtered_ff}),
        .out_x(channelized_data),
        .out_nd(channelized_nd),
        .out_w({channelized_m, channelized_ff}),
        .first(channelized_first),
        .overflow(channelized_error)
        );

   // Keep the channels we want.
   reg [N-1:0]     default_desired_channels;
   reg [N-1:0]     desired_channels;
   reg             unaligned;
   reg [LOGN-1:0]  channel;
   reg             looking_for_first_channel;
   initial
     begin
        channel <= {LOGN{1'b0}};
        default_desired_channels <= {N{1'b1}};
        desired_channels <= default_desired_channels;
        unaligned <= 1'b0;
        looking_for_first_channel <= 1'b1;
     end
   always @ (posedge clk or negedge rst_n)
     begin
        if (~rst_n)
          begin
             channel <= {LOGN{1'b0}};
             desired_channels <= default_desired_channels;
             unaligned <= 1'b0;
             looking_for_first_channel <= 1'b1;
          end
        else
          begin
             if (channelized_nd)
               begin
//                  $display("channelized_ff %d channelized_first %d", channelized_ff, channelized_first);
                  if (channelized_ff != channelized_first)
                    unaligned <= 1'b1;
		  if (channelized_first)
		    if (|channel)
		      unaligned <= 1'b1;
                  if (desired_channels[channel])
                    begin
                       if (looking_for_first_channel)
                         begin
                           looking_for_first_channel <= 1'b0;
                           first_channel <= 1'b1;
                         end
                       else
                         first_channel <= 1'b0;
                       out_data <= channelized_data;
                       out_nd <= 1'b1;
                       out_m <= channelized_m;
                    end
                  else
                    out_nd <= 1'b0;
                  if (&channel)
                    looking_for_first_channel <= 1'b1;
                  channel <= channel + 1;
               end
             else
               out_nd <= 1'b0;
          end
     end

   endmodule