// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This is a wrapper around the channelizer module so that it can be
// accessed from the myhdl test bench.

module qa
  (
   input wire                  clk,
   input wire                  reset,
   output wire [{{width}}-1:0] out_data,
   output wire                 out_nd
   );
   
   wire                        out_error_data_source;
   wire                        out_error_channelizer;
   wire                        out_first_channel;
   wire [{{mwidth}}-1:0]       in_m;
   wire [{{mwidth}}-1:0]       out_m;   
   wire                        rst_n;
   
   assign rst_n = ~reset;

   wire [{{width}}-1:0]        in_data;
   wire                        in_nd;

   data_source 
     #({{sendnth}}, {{logsendnth}}, {{width}},
       {{mwidth}}, {{n_data}}, {{logndata}})
   data_source_i
     (clk, rst_n, in_nd, in_data, in_m, out_error_data_source);
   
   channelizer
     #({{n}}, {{logn}}, {{width}},{{mwidth}}, {{fltlen}})
   dut
     (clk, rst_n, in_data, in_nd, in_m, out_data,
      out_nd, out_m, out_error, out_first_channel);
   
endmodule  