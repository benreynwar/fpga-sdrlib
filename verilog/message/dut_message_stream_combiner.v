// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is simply a wrapper around the message_stream_combiner module
// so that it can be accessed from the myhdl test bench.

module dut_message_stream_combiner;
   reg                          clk;
   reg                          rst_n;
   reg [`WIDTH*`N_STREAMS-1:0]  in_data;
   wire [`WIDTH-1:0]            out_data;
   reg [`N_STREAMS-1:0]         in_nd;
   wire                         out_nd;
   wire                         error;
   
   initial begin
	  $from_myhdl(clk, rst_n, in_data, in_nd);
	  $to_myhdl(out_data, out_nd, error);
   end
   
   message_stream_combiner
     #( `N_STREAMS, `LOG_N_STREAMS, `WIDTH,
        `INPUT_BUFFER_LENGTH, `LOG_INPUT_BUFFER_LENGTH,
        `MAX_PACKET_LENGTH, `LOG_MAX_PACKET_LENGTH)
   dut
     (clk, rst_n, in_data, in_nd, out_data, out_nd, error);
   
endmodule  