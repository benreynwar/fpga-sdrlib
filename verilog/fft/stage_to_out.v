// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// Connects a stage and an mstore to a standard block output.

module stage_to_out
 #(
   parameter N = 8,
   parameter LOG_N = 3,
   parameter WIDTH = 32,
   parameter MWIDTH = 1
   )
   (
    input wire              clk,
    input wire              rst_n,
    // Start signals
    input wire              start,
    // From Stage
    output reg [LOG_N-1:0]  addr,
    input wire [WIDTH-1:0]  in_data,
    // From mStore
    output reg              out_mread,
    input wire [MWIDTH-1:0] in_m,
    // To out
    output reg              out_nd,
    output reg [WIDTH-1:0]  out_data,
    output reg [MWIDTH-1:0] out_m,
    // Finished Signal
    output reg              finished,
    output reg              error
    );

   reg                       active;

   always @ (posedge clk)
     begin
        // Set the default values;
        out_nd <= 1'b0;
        out_mread <= 1'b0;
        finished <= 1'b0;
        if (~rst_n)
          begin
             active <= 1'b0;
             addr <= {LOG_N{1'b0}};
             error <= 1'b0;
          end
        else if (start)
          begin
             if (active)
               error <= 1'b1;
             else
               begin
                  active <= 1'b1;
                  addr <= {LOG_N{1'b0}};
               end
          end
        else if (active)
          begin
             out_mread <= 1'b1;
             out_nd <= 1'b1;
             out_data <= in_data;
             out_m <= in_m;
             if (addr == N-1)
               begin
                  active <= 1'b0;
                  finished <= 1'b1;
               end
             else
               addr <= addr + 1;
          end
     end
endmodule