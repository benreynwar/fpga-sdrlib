// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// An input stream is a mix of samples and messages.
// The first bit of a message header is 1.
// Samples and message contents have a first bit of 0.
// A message header says how many message contents follow.

// The stream is split into a sample stream and a message stream.

module sample_msg_splitter
  #(
    parameter WIDTH = 32
    )
   (
    input                  clk,
    input                  rst_n,
    input wire [WIDTH-1:0] in_data,
    input wire             in_nd,
    output reg [WIDTH-1:0] out_samples,
    output reg             out_samples_nd,
    output reg [WIDTH-1:0] out_msg,
    output reg             out_msg_nd,
    output reg             error       
    );

   // Control stuff
   reg [`MSG_LENGTH_WIDTH-1:0] packet_pos;
   reg [`MSG_LENGTH_WIDTH-1:0] packet_length;

   initial
     begin
        out_samples_nd <= 1'b0;
        out_msg_nd <= 1'b0;
        packet_pos <= {`MSG_LENGTH_WIDTH{1'b0}};
        packet_length <= {`MSG_LENGTH_WIDTH{1'b0}};
     end
   
   always @ (posedge clk)
     begin
        if (in_nd)
          begin
             if (in_data[WIDTH-1])
               begin
                  // In a header.
                  packet_length <= in_data[WIDTH-2 -:`MSG_LENGTH_WIDTH];
                  packet_pos <= 1;
                  out_msg <= in_data;
                  out_msg_nd <= 1'b1;
                  out_samples_nd <= 1'b0;
                  // Already in a packet but we got a header -> error.
                  if (packet_pos != 0)
                    error <= 1'b1;
               end
             else
               begin
                  if (packet_pos == 0)
                    begin
                       out_samples <= in_data;
                       out_samples_nd <= 1'b1;
                       out_msg_nd <= 1'b0;
                    end
                  else
                    begin
                       if (packet_pos == packet_length)
                         begin
                            packet_pos <= {`MSG_LENGTH_WIDTH{1'b0}};
                            packet_length <= {`MSG_LENGTH_WIDTH{1'b0}};
                         end
                       out_msg <= in_data;
                       out_msg_nd <= 1'b1;
                       out_samples_nd <= 1'b0;
                    end
               end 
          end 
        else
          begin
             out_samples_nd <= 1'b0;
             out_msg_nd <= 1'b0;
          end
     end
   
endmodule
