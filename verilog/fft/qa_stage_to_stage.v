// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// Testing with two FFT stages.
// Fill the first one, do one FFT stage move,
// and empty the second one.
// This is for QA purposes.

// PARAMETERS:
//  N - fft length
//  STAGE_INDEX - which FFT stage we're testing.

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

   // Stage 0 to Stage 1
   wire [LOG_N-1:0]              s2ss_addr0;
   wire [LOG_N-1:0]              s2ss_addr1;
   wire [WIDTH-1:0]              s2ss_data0;
   wire [WIDTH-1:0]              s2ss_data1;
   wire [LOG_N-1:0]              ss2s_addr0;
   wire [LOG_N-1:0]              ss2s_addr1;
   wire [WIDTH-1:0]              ss2s_data0;
   wire [WIDTH-1:0]              ss2s_data1;
   wire                          ss2s_nd;
   // Stage 1 to output
   wire [LOG_N-1:0]              s2o_addr0;
   wire [LOG_N-1:0]              s2o_addr1;
   wire [WIDTH-1:0]              s2o_data0;
   wire [WIDTH-1:0]              s2o_data1;
   wire                          error_stage0;
   wire                          error_stage1;
   
   stage #(`N, LOG_N, WIDTH) stage_0
     (
      .clk(clk),
      .rst_n(rst_n),
      .in_addr0(b2s_addr0),
      .in_addr1(b2s_addr1),
      .in_nd(b2s_nd),
      .in_data0(b2s_data0),
      .in_data1(b2s_data1),
      .out_addr0(s2ss_addr0),
      .out_addr1(s2ss_addr1),
      .out_data0(s2ss_data0),
      .out_data1(s2ss_data1),
      .error(error_stage0)
      );

   reg [LOG_N-1:0]               ss_index;
   reg                           ss_mode;
   wire [WIDTH-1:0]              ss2null_data0;
   wire [WIDTH-1:0]              ss2null_data1;
   wire                          ss2null_nd;
   wire                          ss_error;
   reg                           ss_start;
   
   stage_to_stage #(`N, LOG_N, WIDTH) stage_to_stage_0
     (
      .clk(clk),
      .rst_n(rst_n),
      .stage_index(ss_index),
      .start(ss_start),
      .mode(ss_mode),
      .finished(ss_finished),
      .from_addr0(s2ss_addr0),
      .from_addr1(s2ss_addr1),
      .to_addr0(ss2s_addr0),
      .to_addr1(ss2s_addr1),
      .to_data0(ss2s_data0),
      .to_data1(ss2s_data1),
      .from_data0_A(s2ss_data0),
      .from_data1_A(s2ss_data1),
      .to_nd_A(ss2s_nd),
      .from_data0_B(ss2null_data0),
      .from_data1_B(ss2null_data1),
      .to_nd_B(ss2null_nd),
      .error(ss_error)
    );
   
   stage #(`N, LOG_N, WIDTH) stage_1
     (
      .clk(clk),
      .rst_n(rst_n),
      .in_addr0(ss2s_addr0),
      .in_addr1(ss2s_addr1),
      .in_nd(ss2s_nd),
      .in_data0(ss2s_data0),
      .in_data1(ss2s_data1),
      .out_addr0(s2o_addr0),
      .out_addr1(s2o_addr1),
      .out_data0(s2o_data0),
      .out_data1(s2o_data1),
      .error(error_stage1)
      );

   always @ (posedge clk)
     if (ss2s_nd)
       $display("Input to second stage is %d %d at addr %d %d", ss2s_data0, ss2s_data1, ss2s_addr0, ss2s_addr1);
   
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

   localparam  [1:0]  STATE_IN = 0;
   localparam  [1:0]  STATE_SS = 1;
   localparam  [1:0]  STATE_OUT = 2;

   reg [1:0]                     state;                     
   
   always @ (posedge clk)
     begin
        //defaults
        b2s_start <= 1'b0;
        ss_start <= 1'b0;
        s2o_start <= 1'b0;
        if (~rst_n)
          begin
             state <= STATE_IN;
             b2s_start <= 1'b1;
             control_error <= 1'b0;
             ss_index <= `STAGE_INDEX;
             ss_mode <= 1'b0;
             $display("STATE_IN");
          end
        else
          begin
             if (b2s_finished)
               if (state != STATE_IN)
                 control_error <= 1'b1;
               else
                 begin
                    $display("STATE_SS");
                    ss_start <= 1'b1;
                    state <= STATE_SS;
                 end
             if (ss_finished)
               if (state != STATE_SS)
                 control_error <= 1'b1;
               else
                 begin
                    $display("STATE_OUT");
                    s2o_start <= 1'b1;
                    state <= STATE_OUT;
                 end
             if (s2o_finished)
               if (state != STATE_OUT)
                 control_error <= 1'b1;
               else
                 begin
                    $display("STATE_IN");
                    b2s_start <= 1'b1;
                    state <= STATE_IN;
                 end
          end
     end
       
   assign error = buffer_write_error | buffer_read_error | b2s_error | mstore_error | error_stage0 | error_stage1 | s2o_error | control_error | ss_error;

   
endmodule