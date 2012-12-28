// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module message_slicer
  #(
    parameter N_SLICES = 2,
    parameter WIDTH = 32,
    parameter BUFFER_LENGTH = 32
    )
   (
    input                           clk,
    input                           rst_n,
    input wire [WIDTH*N_SLICES-1:0] in_data,
    input wire                      in_nd,
    output reg [WIDTH-1:0]          out_data,
    output reg                      out_nd,
    output wire                     error
    );

   function integer clog2;
      input integer              value;
      begin
         value = value-1;
         for (clog2=0; value>0; clog2=clog2+1)
           value = value>>1;
      end
   endfunction

   localparam integer LOG_N_SLICES = clog2(N_SLICES);

   reg                read_delete;
   wire [N_SLICES*WIDTH-1:0] read_data;
   wire                      read_full;
   
   buffer_BB #(N_SLICES*WIDTH, BUFFER_LENGTH) buffer_0
     (.clk(clk),
      .rst_n(rst_n),
      .write_strobe(in_nd),
      .write_data(in_data),
      .read_delete(read_delete),
      .read_full(read_full),
      .read_data(read_data),
      .error(error)
    );

   reg [LOG_N_SLICES-1:0] pos;
   wire [WIDTH-1:0]       sliced_data[N_SLICES-1:0];

   genvar                 i;
   generate 
      for(i=0; i<N_SLICES; i=i+1) begin: loop_0
         assign sliced_data[i] = read_data[WIDTH*(i+1)-1 -:WIDTH];
      end
   endgenerate
   
   // Send out data from the buffer.
   always @ (posedge clk)
     begin
        out_nd <= 1'b0;
        read_delete <= 1'b0;
        if (!rst_n)
          begin
             pos <= N_SLICES-1;
          end
        else if (read_full)
          begin
             out_nd <= 1'b1;
             out_data <= sliced_data[pos];
             if (pos == 0)
               begin
                  pos <= N_SLICES-1;
                  read_delete <= 1'b1;
               end
             else
               pos <= pos - 1;
          end
     end
    
endmodule
