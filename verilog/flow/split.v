// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module split
  #(
    parameter N_OUT_STREAMS = 2,
    parameter LOG_N_OUT_STREAMS = 1,
    parameter WIDTH = 32
    )
   (
    input                                clk,
    input                                rst_n,
    input wire [WIDTH-1:0]               in_data,
    input wire                           in_nd,
    output reg [WIDTH*N_OUT_STREAMS-1:0] out_data,
    output reg                           out_nd
    );

   reg [LOG_N_OUT_STREAMS-1:0]           pos;
   wire [WIDTH*N_OUT_STREAMS-1:0]        shifted_data;

   assign shifted_data = in_data << WIDTH*pos;
   
   always @ (posedge clk)
     begin
        if (!rst_n)
          begin
             pos <= {LOG_N_OUT_STREAMS{1'b0}};
          end
        else
          if (in_nd)
            begin
               if (pos == N_OUT_STREAMS-1)
                 begin
                    out_data <= out_data + shifted_data;
                    pos <= 1'b0;
                    out_nd <= 1'b1;
                 end
               else if (pos == 0)
                 begin
                    out_data <= shifted_data;
                    out_nd <= 1'b0;
                    pos <= pos + 1;
                 end
               else
                 begin
                    out_data <= out_data + shifted_data;
                    out_nd <= 1'b0;
                    pos <= pos + 1;
                 end
            end
          else
            out_nd <= 1'b0;
     end
   
endmodule
