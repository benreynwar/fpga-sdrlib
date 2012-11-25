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
    output wire                       error       
    );

   // Input Buffers info
   reg [WIDTH-1:0]                   input_buffers [INPUT_BUFFER_LENGTH*N_STREAMS-1:0];
   // When filled and emptied are equal it is empty.
   // When they are opposite it is full.
   reg [INPUT_BUFFER_LENGTH-1:0] input_buffers_filled[N_STREAMS-1:0];
   reg [INPUT_BUFFER_LENGTH-1:0] input_buffers_emptied[N_STREAMS-1:0];
   wire [INPUT_BUFFER_LENGTH-1:0] input_buffers_full[N_STREAMS-1:0];
   reg [LOG_INPUT_BUFFER_LENGTH-1:0]       input_buffers_write_pos[N_STREAMS-1:0];
   reg [LOG_INPUT_BUFFER_LENGTH-1:0]       input_buffers_read_pos[N_STREAMS-1:0];
   reg [N_STREAMS-1:0]                     stream_errors;                    

   assign error = | stream_errors;
   
   genvar                            i, j;

   // Write data to the input buffers.
   generate
      for (j=0; j<N_STREAMS; j=j+1) begin: LOOP_1

         assign input_buffers_full[j] = input_buffers_filled[j] ^ input_buffers_emptied[j];

         initial
           begin
              input_buffers_write_pos[j] <= {LOG_INPUT_BUFFER_LENGTH{1'b0}};
              input_buffers_filled[j] <= {INPUT_BUFFER_LENGTH{1'b0}};
              input_buffers_emptied[j] <= {INPUT_BUFFER_LENGTH{1'b0}};
              stream_errors[j] <= 1'b0;
           end

         always @ (posedge clk)
           begin
              if (!rst_n)
                begin
                   input_buffers_write_pos[j] <= {LOG_INPUT_BUFFER_LENGTH{1'b0}};
                   input_buffers_filled[j] <= {INPUT_BUFFER_LENGTH{1'b0}};
                   input_buffers_emptied[j] <= {INPUT_BUFFER_LENGTH{1'b0}};
                   stream_errors[j] <= 1'b0;
                end
              else
                if (in_nd[j])
                  begin
                     //$display("j is %d input_buffers_full[j] is %d", j, input_buffers_full[j]);
                     //$display("Stream is %d Input buffer write pos %d full is %d", j, input_buffers_write_pos[j], input_buffers_full[j][input_buffers_write_pos[j]]);
                     if (!(input_buffers_full[j][input_buffers_write_pos[j]]))
                       begin
                          //$display("Write to input buffer %d", in_data[WIDTH*(j+1)-1 -:WIDTH]);
                          input_buffers[INPUT_BUFFER_LENGTH*j + input_buffers_write_pos[j]] <= in_data[WIDTH*(j+1)-1 -:WIDTH];
                          input_buffers_write_pos[j] <= input_buffers_write_pos[j] + 1;
                          input_buffers_filled[j][input_buffers_write_pos[j]] <= ~input_buffers_filled[j][input_buffers_write_pos[j]];
                       end
                     else
                       begin
                          stream_errors[j] <= 1'b1;
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
   wire [WIDTH-1:0]                                 i_buffer_read;
   wire [LOG_MAX_PACKET_LENGTH-1:0]                 packet_length_read;
   wire                                             is_header;
   
   assign i_buffer_read_pos = INPUT_BUFFER_LENGTH*stream + input_buffers_read_pos[stream];
   assign i_buffer_read = input_buffers[i_buffer_read_pos];
   assign packet_length_read = i_buffer_read[WIDTH-2 -:LOG_MAX_PACKET_LENGTH];
   assign is_header = i_buffer_read[WIDTH-1];
   
   generate
      for (i=0; i<N_STREAMS; i=i+1) begin: LOOP_2
   // Move data from the inputs buffers to the output stream.

         initial
           input_buffers_read_pos[i] <= {LOG_INPUT_BUFFER_LENGTH{1'b0}};
         
         always @ (posedge clk)
           begin
              if (!rst_n)
                begin
                   input_buffers_read_pos[i] <= {LOG_INPUT_BUFFER_LENGTH{1'b0}};
                end
              else
                if (i == stream)
                  if (input_buffers_full[i][input_buffers_read_pos[i]])
                    input_buffers_read_pos[i] <= input_buffers_read_pos[i] + 1;
           end // always @ (posedge clk)
      end
   endgenerate

   initial
     begin
        packet_pos <= {LOG_MAX_PACKET_LENGTH{1'b0}};
        stream <= {LOG_N_STREAMS{1'b0}};
     end

   always @ (posedge clk)
     begin
        if (!rst_n)
          begin
             packet_pos <= {LOG_MAX_PACKET_LENGTH{1'b0}};
             stream <= {LOG_N_STREAMS{1'b0}};
          end
        else
          begin
             if (input_buffers_full[stream][input_buffers_read_pos[stream]])
               begin
                  input_buffers_emptied[stream][input_buffers_read_pos[stream]] <= ~input_buffers_emptied[stream][input_buffers_read_pos[stream]];
                  out_data <= input_buffers[i_buffer_read_pos];
                  out_nd <= 1'b1;
                  //This is done in a generate loop where we can reset also.
                  //input_buffers_read_pos[stream] <= input_buffers_read_pos[stream] + 1;
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
     end
endmodule
