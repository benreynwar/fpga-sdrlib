// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// A Message stream is a wire of width WIDTH.
// If the first bit is a '1' it is a header.
// The following LOG_MAX_PACKET_LENGTH bits give the
// number of WIDTH bit blocks in the packet.

module message_stream_combiner
  #(
    parameter N_STREAMS = 4,
    parameter LOG_N_STREAMS = 2,
    parameter WIDTH = 32,
    parameter INPUT_BUFFER_LENGTH = 64,
    parameter LOG_INPUT_BUFFER_LENGTH = 6,
    parameter MAX_PACKET_LENGTH = 1024,
    parameter LOG_MAX_PACKET_LENGTH = 10
    )
   (
    input                            clk,
    input                            rst_n,
    input wire [WIDTH*N_STREAMS-1:0] in_data,
    input wire [N_STREAMS-1:0]       in_nd,
    output reg [WIDTH-1:0]           out_data,
    output reg                       out_nd,
    output wire                      error       
    );

   wire [N_STREAMS-1:0]              stream_write_errors;
   wire [N_STREAMS-1:0]              stream_read_errors;
   wire [N_STREAMS-1:0]              stream_errors;
   reg [N_STREAMS-1: 0]              read_deletes;
   wire [N_STREAMS-1: 0]             read_fulls;
   wire [WIDTH-1: 0]                 read_datas[N_STREAMS-1:0];
   reg [LOG_N_STREAMS-1: 0]          stream;

   assign stream_errors = stream_write_errors | stream_read_errors;
   assign error = | stream_errors;
   
   genvar                            i;
   // Set up the input buffers.
   // FIXME: Change this to use buffer_BB so it is faster.
   generate
      for (i=0; i<N_STREAMS; i=i+1) begin: LOOP_0
         buffer_AA #(WIDTH, INPUT_BUFFER_LENGTH, LOG_INPUT_BUFFER_LENGTH)
         the_buffer 
         (.clk(clk),
          .rst_n(rst_n),
          .write_strobe(in_nd[i]),
          .write_data(in_data[WIDTH*(i+1)-1 -:WIDTH]),
          .read_delete(read_deletes[i]),
          .read_full(read_fulls[i]),
          .read_data(read_datas[i]),
          .write_error(stream_write_errors[i]),
          .read_error(stream_read_errors[i])
          );
      end
      
   endgenerate

   reg [LOG_MAX_PACKET_LENGTH-1:0] packet_pos;
   reg [LOG_MAX_PACKET_LENGTH-1:0] packet_length;
   wire                            is_header;
   wire [WIDTH-1:0]                temp_is_header;

   // If I use is_header = read_datas[stream][WIDTH-1] it seems to pick up
   // the least significant bit (irrespective of the value in the second
   // bracket) when I synthesise (but not simulate in Icarus).  So I'm using
   // this alternate method.
   assign temp_is_header = read_datas[stream] >> (WIDTH-1);
   assign is_header = temp_is_header;

   // Deal with reading from input buffers.
   always @ (posedge clk)
     begin
        if (!rst_n)
          begin
             stream <= {LOG_N_STREAMS{1'b0}};
             read_deletes <= {N_STREAMS{1'b0}};
             packet_pos <= {LOG_MAX_PACKET_LENGTH{1'b0}};
             packet_length <= {LOG_MAX_PACKET_LENGTH{1'b0}};
          end
        else
          begin
             // If just deleted then we need to wait a cycle before the
             // buffer displays the new value for reading.
             if ((!read_deletes[stream]) && (read_fulls[stream]))
               begin
                  read_deletes <= {{N_STREAMS-1{1'b0}},{1'b1}} << stream;
                  out_nd <= 1'b1;
                  out_data <= read_datas[stream];
                  if (packet_pos == 0)
                    begin
                       // Check if header (look at header bit)
                       if (is_header)
                         begin
                            packet_length <= read_datas[stream][WIDTH-2 -:LOG_MAX_PACKET_LENGTH];
                            if (read_datas[stream][WIDTH-2 -:LOG_MAX_PACKET_LENGTH] != 0)
                              packet_pos <= packet_pos + 1;
                         end
                    end // if (packet_pos == 0)
                  else
                    begin
                       if (packet_pos == packet_length)
                         packet_pos <= 0;
                       else
                         packet_pos <= packet_pos + 1;
                    end
               end
             else
               begin
                  out_nd <= 1'b0;
                  if (packet_pos == 0)
                    // Move onto next stream.
                    begin
                       if (stream == N_STREAMS-1)
                         stream <= 0;
                       else
                         stream <= stream + 1;
                    end
                  read_deletes <= {N_STREAMS{1'b0}};
               end
          end
     end

endmodule
