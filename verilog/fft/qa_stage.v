// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// A single FFT stage.
// We fill it with values and then empty it.
// This is for QA purposes.

module qa_contents
  #(
    parameter WIDTH = 32,
    parameter MWIDTH = 1
    )
   (
    input wire                   clk,
    input wire                   rst_n,
    input wire [WIDTH-1:0]       in_data,
    input wire                   in_nd,
    input wire [MWIDTH-1:0]      in_m,
    input wire [`MSG_WIDTH-1:0]  in_msg,
    input wire                   in_msg_nd, 
    output wire [WIDTH-1:0]      out_data,
    output wire                  out_nd,
    output wire [MWIDTH-1:0]     out_m,
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd, 
    output wire                  error
    );

   function integer clog2;
      input integer              value;
      begin
         value = value-1;
         for (clog2=0; value>0; clog2=clog2+1)
           value = value>>1;
      end
   endfunction
   
   localparam integer            LOG_N = clog2(`N);

   wire                          buffer_read_delete;
   wire                          buffer_read_full;
   wire [WIDTH+MWIDTH-1:0]       buffer_data;
   wire                          buffer_write_error;
   wire                          buffer_read_error;
   
   buffer_BB #(WIDTH+MWIDTH, `N, LOG_N) buffer_in
     (
      .clk(clk),
      .rst_n(rst_n),
      .write_strobe(in_nd),
      .write_data({in_data, in_m}),
      .read_delete(buffer_read_delete),
      .read_full(buffer_read_full),
      .read_data(buffer_data),
      .write_error(buffer_write_error),
      .read_error(buffer_read_error)
      );

   reg                           b2s_start;
   wire                          b2s_finished;
   wire [LOG_N-1:0]              b2s_addr0;
   wire [LOG_N-1:0]              b2s_addr1;
   wire                          b2s_nd;
   wire [WIDTH-1:0]              b2s_data0;
   wire [WIDTH-1:0]              b2s_data1;
   wire                          b2s_mnd;
   wire [MWIDTH-1:0]             b2s_m;
   wire                          b2s_error;
   
   buffer_BB_to_stage #(`N, LOG_N, WIDTH, MWIDTH) b2s
     (
      .clk(clk),
      .rst_n(rst_n),
      .start(b2s_start),
      .read_full(buffer_read_full),
      .read_data(buffer_data),
      .read_delete(buffer_read_delete),
      .out_addr0(b2s_addr0),
      .out_addr1(b2s_addr1),
      .out_nd(b2s_nd),
      .out_data0(b2s_data0),
      .out_data1(b2s_data1),
      .out_mnd(b2s_mnd),
      .out_m(b2s_m),
      .finished(b2s_finished),
      .error(b2s_error)
      );

   wire                          mstore_read;
   wire                          mstore_error;
   wire [MWIDTH-1:0]             s2o_m;
   
   mstore #(`N, MWIDTH) mstore_0
     (
      .clk(clk),
      .rst_n(rst_n),
      .in_nd(b2s_mnd),
      .in_m(b2s_m),
      .in_read(mstore_read),
      .out_m(s2o_m),
      .error(mstore_error)
      );

   wire [LOG_N-1:0]              s2o_addr0;
   // stage_addrX is connected to s2o_addrX or bs2addrX depending on whether
   // we are writing or reading.
   wire [LOG_N-1:0]              stage_addr0;
   wire [LOG_N-1:0]              stage_addr1;
   wire [WIDTH-1:0]              s2o_data0;
   wire [WIDTH-1:0]              s2o_data1;
   wire                          error_stage;
   
   stage #(`N, LOG_N, WIDTH) stage_0
     (
      .clk(clk),
      .rst_n(rst_n),
      .in_addr0(stage_addr0),
      .in_addr1(stage_addr1),
      .in_nd(b2s_nd),
      .in_data0(b2s_data0),
      .in_data1(b2s_data1),
      .out_data0(s2o_data0),
      .out_data1(s2o_data1),
      .error(error_stage)
      );

   reg                           s2o_start;
   wire                          s2o_finished;
   wire                          s2o_error;
   
   stage_to_out #(`N, LOG_N, WIDTH, MWIDTH) s2o
     (
      .clk(clk),
      .rst_n(rst_n),
      .start(s2o_start),
      .addr(s2o_addr0),
      .in_data(s2o_data0),
      .out_mread(mstore_read),
      .in_m(s2o_m),
      .out_nd(out_nd),
      .out_data(out_data),
      .out_m(out_m),
      .finished(s2o_finished),
      .error(s2o_error)
      );

   reg                           writing;
   reg                           control_error;

   assign stage_addr0 = (writing)?b2s_addr0:s2o_addr0;
   assign stage_addr1 = b2s_addr1;
   
   // The logic to inititate the reading and writing.
   always @ (posedge clk)
     if (~rst_n)
       begin
          writing <= 1'b1;
          b2s_start <= 1'b1;
          control_error <= 1'b0;
       end
     else
       begin
          //defaults
          b2s_start <= 1'b0;
          s2o_start <= 1'b0;
          if (b2s_finished)
            if (~writing)
              control_error <= 1'b1;
            else
              begin
                 s2o_start <= 1'b1;
                 writing <= 1'b0;
              end
          if (s2o_finished)
            if (writing)
              control_error <= 1'b1;
            else
              begin
                 b2s_start <= 1'b1;
                 writing <= 1'b1;
              end
       end
       
   assign error = buffer_write_error | buffer_read_error | b2s_error | mstore_error | error_stage | s2o_error | control_error;

   
endmodule