// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This qa_wrapper takes the data and outputs alternately
// bit position and bit contents.
// If data arrives too frequently then ERRORCODE is output.

module qa_wrapper
  #(
    parameter WIDTH = 32
    )
   (
    input wire             clk,
    input wire             reset,
    input wire [WIDTH-1:0] in_data,
    input wire             in_nd,
    output reg [WIDTH-1:0] out_data,
    output reg             out_nd
    );
   
   reg                      ready;
   reg                      error;
   reg [`LOG_WIDTH-1:0]     bit_pos;
   reg                      pos_not_value;
   reg [WIDTH-1:0]          stored_data;
   
   always @ (posedge clk)
     if (reset)
       begin
          ready <= 1'b1;
          error <= 1'b0;
          out_nd <= 1'b0;
       end
     else if (error)
       begin
          out_nd <= 1'b1;
          out_data <= `ERRORCODE;
       end
     else
       begin
          if (in_nd)
            begin
               if (!ready)
                 error <= 1'b1;
               stored_data <= in_data;
               ready <= 1'b0;
               bit_pos <= WIDTH-1;
               out_nd <= 1;
               out_data <= WIDTH-1;
               pos_not_value <= 0;
            end
          else if (!ready)
            begin
               out_nd <= 1'b1;
               pos_not_value <= ~pos_not_value;
               if (pos_not_value)
                 begin
                    out_data <= bit_pos;
                 end
               else
                 begin
                    out_data <= stored_data[bit_pos];
                    if (!(|bit_pos))
                      ready <= 1'b1;
                    else
                      bit_pos <= bit_pos - 1;
                 end
            end
          else
            out_nd <= 1'b0;
       end
        
endmodule