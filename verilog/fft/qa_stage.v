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
   
   localparam integer            STAGE_EMPTY = 2'd0;
   localparam integer            STAGE_WRITING = 2'd1;
   localparam integer            STAGE_FULL = 2'd2;
   localparam integer            STAGE_READING = 2'd3;

   wire                          buffer_read_delete;
   wire                          buffer_read_full;
   wire [WIDTH+MWIDTH-1:0]       buffer_data;
   wire                          buffer_error;
   
   buffer_BB #(WIDTH+MWIDTH, `N) buffer_in
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

   wire [LOG_N-1:0]              s2o_addr0;
   wire [LOG_N-1:0]              s2o_addr1; // not used
   wire [WIDTH-1:0]              s2o_data0;
   wire [WIDTH-1:0]              s2o_data1;
   wire                          error_stage;
   wire [1:0]                    s_state;
   wire                          s2o_active;

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
      .out_addr0(s2o_addr0),
      .out_addr1(s2o_addr1),
      .out_data0(s2o_data0),
      .out_data1(s2o_data1),
      .out_active(s2o_active),
      .state(s_state),
      .error(error_stage)
      );

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
      .in_m(s2o_m),
      .out_nd(out_nd),
      .out_data(out_data),
      .out_m(out_m),
      .active(s2o_active),
      .error(s2o_error)
      );

   reg                           writing;

   assign stage_addr0 = (writing)?b2s_addr0:s2o_addr0;
   assign stage_addr1 = b2s_addr1;
   
   // The logic to inititate the reading and writing.
   always @ (posedge clk)
     if (~rst_n)
       begin
          writing <= 1'b1;
          b2s_start <= 1'b1;
          s2o_start <= 1'b0;
       end
     else
       begin
          //defaults
          b2s_start <= 1'b0;
          s2o_start <= 1'b0;
          if (s_state == STAGE_EMPTY)
            b2s_start <= 1'b1;
          else if (s_state == STAGE_FULL)
            s2o_start <= 1'b1;
       end
       
   assign error = buffer_error | b2s_error | mbuffer_error | error_stage | s2o_error;
   
endmodule