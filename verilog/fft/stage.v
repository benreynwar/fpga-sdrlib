// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// A single stage for a FFT.

module stage
  #(
    parameter N = 8,
    parameter LOG_N = 3,
    parameter WIDTH = 32
    )
   (
    input wire              clk,
    input wire              rst_n,
    input wire [LOG_N-1:0]  in_addr0,
    input wire [LOG_N-1:0]  in_addr1, 
    input wire              in_nd,
    input wire [WIDTH-1:0]  in_data0,
    input wire [WIDTH-1:0]  in_data1,
    output wire [WIDTH-1:0] out_data0,
    output wire [WIDTH-1:0] out_data1,
    output reg              error
    );

   reg [WIDTH-1:0]           RAM[N-1:0];    
   
   assign out_data0 = RAM[in_addr0];
   assign out_data1 = RAM[in_addr1];
   
   always @ (posedge clk)
     if (~rst_n)
       begin
          error <= 1'b0;
       end
     else
       begin
          if (in_nd)
            begin
               RAM[in_addr0] <= in_data0;
               RAM[in_addr1] <= in_data1;
            end
       end
   
endmodule