// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module message_slicer
  #(
    parameter N_SLICES = 2,
    parameter WIDTH = 33,
    parameter BUFFER_LENGTH = 64,
    parameter LOG_BUFFER_LENGTH = 6
    )
   (
    input                           clk,
    input                           rst_n,
    input wire [WIDTH*N_SLICES-1:0] in_data,
    input wire                      in_nd,
    output reg [WIDTH-1:0]          out_data,
    output reg                      out_nd,
    output reg                      error
    );

   // Buffer Info
   reg [WIDTH*BUFFER_LENGTH-1:0]    buffer;
   reg [BUFFER_LENGTH-1:0]          buffer_full;
   reg [LOG_BUFFER_LENGTH-1:0]      buffer_write_pos;
   reg [LOG_BUFFER_LENGTH-1:0]      buffer_read_pos;
   reg                              old_nd;

   initial
     begin
        buffer_full <= {N_SLICES{1'b0}};
        buffer_write_pos <= {LOG_BUFFER_LENGTH{1'b0}};
        buffer_read_pos <= {LOG_BUFFER_LENGTH{1'b0}};
        old_nd <= 1'b0;
     end
   
   // Write data to the buffer.
   genvar i;
   generate
      for (i=0; i<N_SLICES; i=i+1) begin: LOOP_0

         wire [LOG_BUFFER_LENGTH-1:0] shifted_buffer_write_pos;
         assign shifted_buffer_write_pos = buffer_write_pos + N_SLICES - i - 1;
         
         always @ (posedge clk)
           begin
              if (in_nd != old_nd)
                begin
                   if (buffer_full[buffer_write_pos+i])
                     error <= 1'b1;
                   else
                     begin
                        buffer[(shifted_buffer_write_pos+1)*WIDTH-1 -:WIDTH] <= in_data[(i+1)*WIDTH-1 -:WIDTH];
                        buffer_full[shifted_buffer_write_pos] <= 1'b1;
                     end
                end
           end
      end
   endgenerate

   always @ (posedge clk)
     if (in_nd != old_nd)
       begin
          buffer_write_pos <= buffer_write_pos + N_SLICES;
          old_nd <= in_nd;
       end
   
   // Send out data from the buffer.
   always @ (posedge clk)
     begin
        //$display("reading at %d. full is %d, value is %d", buffer_read_pos, buffer_full[buffer_read_pos], buffer[(buffer_read_pos+1)*WIDTH-1 -:WIDTH]);
        if (buffer_full[buffer_read_pos])
          begin
             buffer_full[buffer_read_pos] <= 1'b0;
             out_data <= buffer[WIDTH*(buffer_read_pos+1)-1 -:WIDTH];
             //$display("Sending the data %d", buffer[WIDTH*(buffer_read_pos+1)-1 -:WIDTH]);
             out_nd <= 1'b1;
             buffer_read_pos <= buffer_read_pos + 1;
          end
        else
          begin
             out_nd <= 1'b0;
          end
      end
    
endmodule
