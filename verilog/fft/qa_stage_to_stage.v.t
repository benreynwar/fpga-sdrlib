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

   // The input buffer
   wire                          buffer_read_delete;
   wire                          buffer_read_full;
   wire [WIDTH+MWIDTH-1:0]       buffer_data;
   wire                          buffer_error;
   
   buffer_BB #(WIDTH+MWIDTH, `N, LOG_N) buffer_in
     (
      .clk(clk),
      .rst_n(rst_n),
      .write_strobe(in_nd),
      .write_data({in_data, in_m}),
      .read_delete(buffer_read_delete),
      .read_full(buffer_read_full),
      .read_data(buffer_data),
      .error(buffer_error)
      );

   // Tranfer from the buffer to the first stage (and to the meta-data buffer).
   reg                           b2s_start;
   wire                          b2s_active;
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
      .active(b2s_active),
      .error(b2s_error)
      );

   // The meta-data buffer.
   wire                          mbuffer_read;
   wire                          mbuffer_error;
   wire                          mbuffer_full;
   wire [MWIDTH-1:0]             s2o_m;
   
   buffer_BB #(MWIDTH, `N*2) mstore
     (
      .clk(clk),
      .rst_n(rst_n),
      .write_strobe(b2s_mnd),
      .write_data(b2s_m),
      .read_delete(mbuffer_read),
      .read_full(mbuffer_full),
      .read_data(s2o_m),
      .error(mbuffer_error)
      );

   // The first stage.
   wire [LOG_N-1:0]              s2ss_addr0;
   wire [LOG_N-1:0]              s2ss_addr1;
   wire [WIDTH-1:0]              s2ss_data0;
   wire [WIDTH-1:0]              s2ss_data1;
   wire                          error_stage0;
   wire [1:0]                    state_stage0;
   wire                          ss_active;
   
   stage #(`N, LOG_N, WIDTH) stage_0
     (
      .clk(clk),
      .rst_n(rst_n),
      .in_addr0(b2s_addr0),
      .in_addr1(b2s_addr1),
      .in_nd(b2s_nd),
      .in_data0(b2s_data0),
      .in_data1(b2s_data1),
      .in_active(b2s_active),
      .out_addr0(s2ss_addr0),
      .out_addr1(s2ss_addr1),
      .out_data0(s2ss_data0),
      .out_data1(s2ss_data1),
      .out_active(ss_active),
      .state(state_stage0),
      .error(error_stage0)
      );

   // Tranfer from the first stage to the second stage.
   wire [LOG_N-1:0]              ss2s_addr0;
   wire [LOG_N-1:0]              ss2s_addr1;
   wire [WIDTH-1:0]              ss2s_data0;
   wire [WIDTH-1:0]              ss2s_data1;
   wire                          ss2s_nd;

   reg [LOG_N-1:0]               ss_index;
   reg                           ss_mode;
   wire [WIDTH-1:0]              ss2null_data0;
   wire [WIDTH-1:0]              ss2null_data1;
   wire                          ssnull_start;
   wire                          ssnull_active;
   wire                          ss_error;
   reg                           ss_start;

   assign ssnull_start = 1'b0;
   
   stage_to_stage_{{N}} #(`N, LOG_N, WIDTH) stage_to_stage_0
     (
      .clk(clk),
      .rst_n(rst_n),
      .stage_index(ss_index),
      .start_A(ss_start),
      .start_B(ssnull_start),
      .from_addr0(s2ss_addr0),
      .from_addr1(s2ss_addr1),
      .to_addr0(ss2s_addr0),
      .to_addr1(ss2s_addr1),
      .to_data0(ss2s_data0),
      .to_data1(ss2s_data1),
      .from_data0_A(s2ss_data0),
      .from_data1_A(s2ss_data1),
      .to_nd(ss2s_nd),
      .active_A(ss_active),
      .from_data0_B(ss2null_data0),
      .from_data1_B(ss2null_data1),
      .active_B(ssnull_active),
      .error(ss_error)
    );

   // The Second Stage.
   wire [LOG_N-1:0]              s2o_addr0;
   wire [LOG_N-1:0]              s2o_addr1;
   wire [WIDTH-1:0]              s2o_data0;
   wire [WIDTH-1:0]              s2o_data1;
   wire                          error_stage1;
   wire [1:0]                    state_stage1;
   wire                          s2o_active;
   
   stage #(`N, LOG_N, WIDTH) stage_1
     (
      .clk(clk),
      .rst_n(rst_n),
      .in_addr0(ss2s_addr0),
      .in_addr1(ss2s_addr1),
      .in_nd(ss2s_nd),
      .in_data0(ss2s_data0),
      .in_data1(ss2s_data1),
      .in_active(ss_active),
      .out_addr0(s2o_addr0),
      .out_addr1(s2o_addr1),
      .out_data0(s2o_data0),
      .out_data1(s2o_data1),
      .out_active(s2o_active),
      .state(state_stage1),
      .error(error_stage1)
      );

   // Transfer from the second stage to the output.
   reg                           s2o_start;
   wire                          s2o_error;
   
   stage_to_out #(`N, LOG_N, WIDTH, MWIDTH) s2o
     (
      .clk(clk),
      .rst_n(rst_n),
      .start(s2o_start),
      .addr(s2o_addr0),
      .in_data(s2o_data0),
      .out_mread(mbuffer_read),
      .in_mfull(mbuffer_full),
      .in_m(s2o_m),
      .out_nd(out_nd),
      .out_data(out_data),
      .out_m(out_m),
      .active(s2o_active),
      .error(s2o_error)
      );

   localparam integer       STAGE_EMPTY = 2'd0;
   localparam integer       STAGE_WRITING = 2'd1;
   localparam integer       STAGE_FULL = 2'd2;
   localparam integer       STAGE_READING = 2'd3;
   
   always @ (posedge clk)
     begin
        //defaults
        b2s_start <= 1'b0;
        ss_start <= 1'b0;
        s2o_start <= 1'b0;
        //$display("errors %d %d %d %d %d %d %d", buffer_error, b2s_error, mbuffer_error, error_stage0, error_stage1, s2o_error, ss_error);
        //$display("states are %d %d", state_stage0, state_stage1);
        //$display("b2s_start is %d ss_start is %d s2o_start is %d", b2s_start, ss_start, s2o_start);
        //$display("b2s_active is %d ss_active is %d s2o_active is %d", b2s_active, ss_active, s2o_active);
        if (~rst_n)
          begin
             b2s_start <= 1'b1;
             ss_index <= `STAGE_INDEX;
          end
        else
          begin
             if (state_stage0 == STAGE_EMPTY)
               b2s_start <= 1'b1;
             if ((state_stage0 == STAGE_FULL) & (state_stage1 == STAGE_EMPTY))
               ss_start <= 1'b1;
             if (state_stage1 == STAGE_FULL)
               s2o_start <= 1'b1;
          end
     end
       
   assign error = buffer_error | b2s_error | mbuffer_error | error_stage0 | error_stage1 | s2o_error | ss_error;

   
endmodule