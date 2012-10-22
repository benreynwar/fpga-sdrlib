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
    output reg                       error       
    );

   // Input Buffers info
   reg [WIDTH-1:0]                   input_buffers [INPUT_BUFFER_LENGTH*N_STREAMS-1:0];
   reg [INPUT_BUFFER_LENGTH*N_STREAMS-1:0] input_buffers_full;
   reg [LOG_INPUT_BUFFER_LENGTH-1:0]       input_buffers_write_pos[N_STREAMS-1:0];
   reg [LOG_INPUT_BUFFER_LENGTH-1:0]       input_buffers_read_pos[N_STREAMS-1:0];


   genvar                            i, j;

   initial
     begin
        input_buffers_full <= {INPUT_BUFFER_LENGTH * N_STREAMS{1'b0}};
        error <= 1'b0;
     end
   
   generate
      for (i=0; i<N_STREAMS; i=i+1) begin: LOOP_0
      initial
        begin
           input_buffers_write_pos[i] <= {LOG_INPUT_BUFFER_LENGTH{1'b0}};
           input_buffers_read_pos[i] <= {LOG_INPUT_BUFFER_LENGTH{1'b0}};
        end
   end
   endgenerate

   // Write data to the input buffers.
   generate
      for (j=0; j<N_STREAMS; j=j+1) begin: LOOP_1

      always @ (posedge clk)
        begin
           if (in_nd[j])
             begin
                //$display("Stream is %d Input buffer write pos %d full is %d", j, i_buffer_write_pos, input_buffers_full[i_buffer_write_pos]);
                if (!(input_buffers_full[INPUT_BUFFER_LENGTH*j + input_buffers_write_pos[j]]))
                  begin
                     //$display("Write to input buffer %d", in_data[WIDTH*(j+1)-1 -:WIDTH]);
                     input_buffers[INPUT_BUFFER_LENGTH*j + input_buffers_write_pos[j]] <= in_data[WIDTH*(j+1)-1 -:WIDTH];
                     input_buffers_write_pos[j] <= input_buffers_write_pos[j] + 1;
                     input_buffers_full[INPUT_BUFFER_LENGTH*j + input_buffers_write_pos[j]] <= 1'b1;
                  end
                else
                  begin
                     error <= 1'b1;
                  end
             end
        end
   end
   endgenerate
   
   // Control stuff
   reg [LOG_N_STREAMS-1:0]            stream;
   reg [LOG_MAX_PACKET_LENGTH-1:0]    packet_pos;
   reg [LOG_MAX_PACKET_LENGTH-1:0]    packet_length;
   wire [LOG_INPUT_BUFFER_LENGTH+LOG_N_STREAMS-1:0] i_buffer_read_pos;
   wire [WIDTH-1:0]                                i_buffer_read;
   wire [LOG_MAX_PACKET_LENGTH-1:0]                packet_length_read;
   wire                                            is_header;

   assign i_buffer_read_pos = INPUT_BUFFER_LENGTH*stream + input_buffers_read_pos[stream];
   assign i_buffer_write_pos = INPUT_BUFFER_LENGTH*stream + input_buffers_write_pos[stream];
   assign i_buffer_read = input_buffers[i_buffer_read_pos];
   assign packet_length_read = i_buffer_read[WIDTH-2 -:LOG_MAX_PACKET_LENGTH];
   assign is_header = i_buffer_read[WIDTH-1];
   
   initial
     begin
        packet_pos <= {LOG_MAX_PACKET_LENGTH{1'b0}};
        stream <= {LOG_N_STREAMS{1'b0}};
     end

   
   // Move data from dthe inputs buffers to the output stream.
   always @ (posedge clk)
     begin
        //$display("stream %d input buffer full is %d packet pos is %d read pos is %d", stream, input_buffers_full[i_buffer_read_pos], packet_pos, i_buffer_read_pos);
        //$display("first input buffers full are %d %d", input_buffers_full[0], input_buffers_full[64]);
        if (input_buffers_full[i_buffer_read_pos])
          begin
             input_buffers_full[i_buffer_read_pos] <= 1'b0;
             out_data <= input_buffers[i_buffer_read_pos];
             out_nd <= 1'b1;
             input_buffers_read_pos[stream] <= input_buffers_read_pos[stream] + 1;
             if (packet_pos == 0)
               begin
                  //$display("Packet pos is 0");
                  if (is_header)
                    begin
                       //$display("Stream %d - Packet length %d log max %d", stream, packet_length_read, LOG_MAX_PACKET_LENGTH);
                       packet_length <= packet_length_read;
                       if (packet_length_read != 0)
                         packet_pos <= packet_pos + 1;
                    end
               end // if (packet_pos == 0)
             else
               begin
                  //$display("In a packet");
                  if (packet_pos == packet_length)
                    packet_pos <= 0;
                  else
                    packet_pos <= packet_pos + 1;
               end
          end // if (input_buffers_full[i_buffer_read_pos])
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
                  //$display("stream is %d", stream);
               end
          end
     end
   
endmodule
