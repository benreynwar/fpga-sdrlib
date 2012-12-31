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

module dit_series_{{N}}
  #(
    parameter WIDTH = 32,
    parameter MWIDTH = 1,
    parameter N = 8
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

   localparam integer            LOG_N = clog2(N);
   // The number of transforms between stages.
   localparam integer            N_STEPS = LOG_N;
   // The number of stage_to_stage modules
   localparam integer            N_SS = (N_STEPS+1)/2;
   // The number of stage_to_stage modules used in both mode A and mode B.
   localparam integer            N_SS_BOTH = N_STEPS/2;
   // The number of stage modules
   localparam integer            N_S = N_STEPS+1;
   
   // The input buffer
   wire                          buffer_read_delete;
   wire                          buffer_read_full;
   wire [WIDTH+MWIDTH-1:0]       buffer_data;
   wire                          buffer_error;
   
   buffer_BB #(WIDTH+MWIDTH, N) buffer_in
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

   // The data flow between stages and stage_to_stages..
   wire [LOG_N-1:0]              s_in_addr0[N_S-1:0];
   wire [LOG_N-1:0]              s_in_addr1[N_S-1:0];
   wire [WIDTH-1:0]              s_in_data0[N_S-1:0];
   wire [WIDTH-1:0]              s_in_data1[N_S-1:0];
   wire [N_S-1:0]                s_in_nd;
   wire [LOG_N-1:0]              s_out_addr0[N_S-1:0];
   wire [LOG_N-1:0]              s_out_addr1[N_S-1:0];
   wire [WIDTH-1:0]              s_out_data0[N_S-1:0];
   wire [WIDTH-1:0]              s_out_data1[N_S-1:0];
   wire [N_S-1:0]                s_in_active;
   wire [N_S-1:0]                s_out_active;
   wire [LOG_N-1:0]              ss_in_addr0[N_SS-1:0];
   wire [LOG_N-1:0]              ss_in_addr1[N_SS-1:0];
   wire [WIDTH-1:0]              ss_in_data0_A[N_SS-1:0];
   wire [WIDTH-1:0]              ss_in_data1_A[N_SS-1:0];
   wire [WIDTH-1:0]              ss_in_data0_B[N_SS-1:0];
   wire [WIDTH-1:0]              ss_in_data1_B[N_SS-1:0];
   wire [LOG_N-1:0]              ss_out_addr0[N_SS-1:0];
   wire [LOG_N-1:0]              ss_out_addr1[N_SS-1:0];
   wire [WIDTH-1:0]              ss_out_data0[N_SS-1:0];
   wire [WIDTH-1:0]              ss_out_data1[N_SS-1:0];
   wire [N_SS-1:0]            ss_out_nd;

   // Tranfer from the buffer to the first stage (and to the meta-data buffer).
   reg                           b2s_start;
   wire                          b2s_mnd;
   wire [MWIDTH-1:0]             b2s_m;
   wire                          b2s_error;
   
   buffer_BB_to_stage #(N, LOG_N, WIDTH, MWIDTH) b2s
     (
      .clk(clk),
      .rst_n(rst_n),
      .start(b2s_start),
      .read_full(buffer_read_full),
      .read_data(buffer_data),
      .read_delete(buffer_read_delete),
      .out_addr0(s_in_addr0[0]),
      .out_addr1(s_in_addr1[0]),
      .out_nd(s_in_nd[0]),
      .out_data0(s_in_data0[0]),
      .out_data1(s_in_data1[0]),
      .out_mnd(b2s_mnd),
      .out_m(b2s_m),
      .active(s_in_active[0]),
      .error(b2s_error)
      );

   // The meta-data buffer.
   wire                          mbuffer_read;
   wire                          mbuffer_error;
   wire                          mbuffer_full;
   wire [MWIDTH-1:0]             s2o_m;
   
   buffer_BB #(MWIDTH, N*2) mstore
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

   // Stage properties
   wire [N_S-1:0]                s_error;
   wire [1:0]                    s_state[N_S-1:0];

   // Stage to stage properties
   wire [N_SS-1:0]            ss_error;
   wire [N_SS-1:0]            ss_active_A;
   wire [N_SS-1:0]            ss_active_B;

   reg [N_SS-1:0]             ss_start_A;
   reg [N_SS-1:0]             ss_start_B;
   reg [LOG_N-1:0]            ss_index[N_SS-1:0];

   genvar                        i;
   generate
      for (i=0; i<N_SS_BOTH; i=i+1) begin: loop_0
         assign s_in_active[2*i+2] = ss_active_B[i];
      end
      for (i=0; i<N_SS; i=i+1) begin: loop_1
         assign s_in_active[2*i+1] = ss_active_A[i];
         assign s_out_active[2*i] = ss_active_A[i];
         assign s_out_active[2*i+1] = ss_active_B[i];
         assign ss_in_data0_A[i] = s_out_data0[2*i];
         assign ss_in_data1_A[i] = s_out_data1[2*i];
         assign ss_in_data0_B[i] = s_out_data0[2*i+1];
         assign ss_in_data1_B[i] = s_out_data1[2*i+1];
         // Transfer between stages.
         stage_to_stage_{{N}} #(N, LOG_N, WIDTH) stage_to_stage_0
           (
            .clk(clk),
            .rst_n(rst_n),
            .stage_index(ss_index[i]),
            .start_A(ss_start_A[i]),
            .start_B(ss_start_B[i]),
            .from_addr0(ss_in_addr0[i]),
            .from_addr1(ss_in_addr1[i]),
            .to_addr0(ss_out_addr0[i]),
            .to_addr1(ss_out_addr1[i]),
            .to_data0(ss_out_data0[i]),
            .to_data1(ss_out_data1[i]),
            .from_data0_A(ss_in_data0_A[i]),
            .from_data1_A(ss_in_data1_A[i]),
            .to_nd(ss_out_nd[i]),
            .active_A(ss_active_A[i]),
            .from_data0_B(ss_in_data0_B[i]),
            .from_data1_B(ss_in_data1_B[i]),
            .active_B(ss_active_B[i]),
            .error(ss_error[i])
            );
      end

      for (i=1; i<N_S; i=i+1) begin: loop_2
         assign s_in_addr0[i] = ss_out_addr0[(i-1)/2];
         assign s_in_addr1[i] = ss_out_addr1[(i-1)/2];
         assign s_in_data0[i] = ss_out_data0[(i-1)/2];
         assign s_in_data1[i] = ss_out_data1[(i-1)/2];
         assign s_in_nd[i] = ss_out_nd[(i-1)/2];
      end

      for (i=0; i<N_S-1; i=i+1) begin: loop_3
         assign s_out_addr0[i] = ss_in_addr0[i/2];
         assign s_out_addr1[i] = ss_in_addr1[i/2];
      end

      for (i=0; i<N_S; i=i+1) begin: loop_4
         stage #(N, LOG_N, WIDTH) stage_i
             (
              .clk(clk),
              .rst_n(rst_n),
              .in_addr0(s_in_addr0[i]),
              .in_addr1(s_in_addr1[i]),
              .in_nd(s_in_nd[i]),
              .in_data0(s_in_data0[i]),
              .in_data1(s_in_data1[i]),
              .in_active(s_in_active[i]),
              .out_addr0(s_out_addr0[i]),
              .out_addr1(s_out_addr1[i]),
              .out_data0(s_out_data0[i]),
              .out_data1(s_out_data1[i]),
              .out_active(s_out_active[i]),
              .state(s_state[i]),
              .error(s_error[i])
              );
      end
   endgenerate
   
   // Transfer from the final stage to the output.
   reg                           s2o_start;
   wire                          s2o_error;
   
   stage_to_out #(N, LOG_N, WIDTH, MWIDTH) s2o
     (
      .clk(clk),
      .rst_n(rst_n),
      .start(s2o_start),
      .addr(s_out_addr0[N_S-1]),
      .in_data(s_out_data0[N_S-1]),
      .out_mread(mbuffer_read),
      .in_mfull(mbuffer_full),
      .in_m(s2o_m),
      .out_nd(out_nd),
      .out_data(out_data),
      .out_m(out_m),
      .active(s_out_active[N_S-1]),
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
        s2o_start <= 1'b0;
        //$display("States are %d %d %d %d %d", s_state[0], s_state[1], s_state[2], s_state[3], s_state[4]);
        if (~rst_n)
          begin
          end
        else
          begin
             if (s_state[0] == STAGE_EMPTY)
               begin
                  b2s_start <= 1'b1;
               end
             if (s_state[N_S-1] == STAGE_FULL)
               begin
                  s2o_start <= 1'b1;
               end
          end
     end

   generate
      for (i=0; i<N_SS_BOTH; i=i+1) begin: loop_5
         always @ (posedge clk)
           begin
              //defaults
              ss_start_A[i] <= 1'b0;
              ss_start_B[i] <= 1'b0;
              if (~rst_n)
                begin
                end
              else
                begin
                   if ((s_state[2*i] == STAGE_FULL) & (s_state[2*i+1] == STAGE_EMPTY))
                     begin
                        ss_start_A[i] <= 1'b1;
                        ss_index[i] <= 2*i;
                     end
                   if ((s_state[2*i+1] == STAGE_FULL) & (s_state[2*i+2] == STAGE_EMPTY))
                     begin
                        ss_start_B[i] <= 1'b1;
                        ss_index[i] <= 2*i+1;
                     end
                end
           end
      end
      if (N_SS != N_SS_BOTH) begin: if_0
         always @ (posedge clk)
           begin
              //defaults
              ss_start_A[N_SS-1] <= 1'b0;
              ss_start_B[N_SS-1] <= 1'b0;
              if (~rst_n)
                begin
                end
              else if ((s_state[N_S-2] == STAGE_FULL) & (s_state[N_S-1] == STAGE_EMPTY))
                begin
                   ss_start_A[N_SS-1] <= 1'b1;
                   ss_index[N_SS-1] <= N_S-2;
                end
           end
      end
   endgenerate

   wire s_errors_all = | s_error;
   wire ss_errors_all = | ss_error;
            
   assign error = buffer_error | b2s_error | mbuffer_error | s_errors_all | ss_errors_all | s2o_error;

   
endmodule