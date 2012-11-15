// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module message_slicer
  #(
    parameter N_SLICES = 2,
    parameter LOG_N_SLICES = 1,
    parameter WIDTH = 32,
    parameter BUFFER_LENGTH = 32,
    parameter LOG_BUFFER_LENGTH = 5
    )
   (
    input                           clk,
    input                           rst_n,
    input wire [WIDTH*N_SLICES-1:0] in_data,
    // a change in in_nd indicates there is new data on in_data.
    input wire                      in_nd,
    output reg [WIDTH-1:0]          out_data,
    output reg                      out_nd,
    output reg                      error
    );
   
   // Buffer Info
   reg [WIDTH*N_SLICES-1:0]         buffer[BUFFER_LENGTH-1:0];
   reg [BUFFER_LENGTH-1:0]          buffer_filled;
   reg [BUFFER_LENGTH-1:0]          buffer_emptied;
   wire [BUFFER_LENGTH-1:0]         buffer_full;
   reg [LOG_BUFFER_LENGTH-1:0]      buffer_write_pos;
   reg [LOG_BUFFER_LENGTH-1:0]      buffer_read_pos;
   reg [LOG_N_SLICES-1:0]           buffer_read_pos_b;
   reg                              old_nd;

   assign buffer_full = buffer_filled ^ buffer_emptied;
   
   initial
     begin
        buffer_filled <= {N_SLICES{1'b0}};
        buffer_emptied <= {N_SLICES{1'b0}};
        buffer_write_pos <= {LOG_BUFFER_LENGTH{1'b0}};
        buffer_read_pos <= {LOG_BUFFER_LENGTH{1'b0}};
        buffer_read_pos_b <= {LOG_N_SLICES{1'b0}};
        old_nd <= 1'b0;
     end
   
   // Write data to the buffer.
   always @ (posedge clk)
     begin
        if (in_nd != old_nd)
          begin
             if (buffer_full[buffer_write_pos])
               error <= 1'b1;
             else
               begin
                  buffer[buffer_write_pos] <= in_data;
                  buffer_filled[buffer_write_pos] <= ~buffer_filled[buffer_write_pos];
                  buffer_write_pos <= buffer_write_pos + 1;
                  old_nd <= in_nd;
               end
          end
     end

   // Send out data from the buffer.
   always @ (posedge clk)
     begin
        //$display("reading at %d %d. full is %d, value is %d", buffer_read_pos, buffer_read_pos_b, buffer_full[buffer_read_pos], buffer[buffer_read_pos][(buffer_read_pos_b+1)*WIDTH-1 -:WIDTH]);
        if (buffer_full[buffer_read_pos])
          begin
             out_data <= buffer[buffer_read_pos][(N_SLICES-buffer_read_pos_b)*WIDTH-1 -:WIDTH];
             if (buffer_read_pos_b == N_SLICES - 1)
               begin
                  buffer_read_pos_b <= {LOG_N_SLICES{1'B0}};
                  buffer_read_pos <= buffer_read_pos + 1;
                  buffer_emptied[buffer_read_pos] <= ~buffer_emptied[buffer_read_pos];
               end
             else
               begin
                  buffer_read_pos_b <= buffer_read_pos_b + 1;
               end
             //$display("Sending the data %d", buffer[WIDTH*(buffer_read_pos+1)-1 -:WIDTH]);
             out_nd <= 1'b1;
          end
        else
          begin
             out_nd <= 1'b0;
          end
      end
    
endmodule
