// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// The connection between two FFT stages.
// Takes care of all the butterfly magic.

// One module has two modes.
// For example in mode A the connection make be stageW -> stageX
// and in mode B the connection from stageY -> stageZ.
// The is because each connection is only active half the time (A stage
// is either begin written or read to, not both at the same time).

module stage_to_stage_{{N}}
  #(
    parameter N = 8,
    parameter LOG_N = 3,
    parameter WIDTH = 32
    )
   (input wire clk,
    input wire              rst_n,
    // Control signals
    input wire [LOG_N-1:0]  stage_index,
    input wire              start_A,
    input wire              start_B,
    // Mode A and B
    output wire [LOG_N-1:0] from_addr0,
    output wire [LOG_N-1:0] from_addr1,
    output wire [LOG_N-1:0] to_addr0,
    output wire [LOG_N-1:0] to_addr1,
    output wire [WIDTH-1:0] to_data0,
    output wire [WIDTH-1:0] to_data1,
    output wire             to_nd,
    // Mode A
    input wire [WIDTH-1:0]  from_data0_A,
    input wire [WIDTH-1:0]  from_data1_A,
    output wire             active_A,
    // Mode B
    input wire [WIDTH-1:0]  from_data0_B,
    input wire [WIDTH-1:0]  from_data1_B,
    output wire             active_B,
    // Other
    output wire             error
    );

   reg                      mode;
   
   // The connection of these depends on the mode.
   wire [WIDTH-1:0]         from_data0;
   wire [WIDTH-1:0]         from_data1;

   assign from_data0 = (mode)?from_data0_B:from_data0_A;
   assign from_data1 = (mode)?from_data1_B:from_data1_A;
                            
   // Output address send to butterfly
   reg [LOG_N-1:0]          to_addr0_bf;
   wire [LOG_N-1:0]         to_addr1_bf;
   wire [LOG_N-2:0] tf_addr;

   reg              active;
   assign active_A = (((~mode) & active) | start_A);
   assign active_B = ((mode & active) | start_B);
   // Number of series in the stage we are writing to.
   reg [LOG_N-1:0]          S;
   // Contains a 1 for the bits that give j from from_addr0 (i.e. which series).
   reg [LOG_N-1:0]          series_bits;			
   
   /*
    Calculation that determine which positions we should read from and write to
    for with the butterfly module.
    
    If we have a series x_n that we want to get the DFT of, X_k we can write X_k in
    terms of E_k and O_k where E_k and O_k are the DFTs of the even and odd components
    of x_n respectively.

    for k<N/2  : X_k = E_k + exp(-2*pi*i*k/N)*O_k
    for k>=N/2 : X_k = E_{k-N/2} - exp(-2*pi*{k-N/2}/N)*O_{k-N/2}
    We use this relationship to calculate the DFT of x_n in a series of stages.  AFter the
    final stage the output is X_k.  After the second to last stage the output is an
    interleaving of E_k and O_k.
    
    At some general stage we have S interleaved series.
    
    So if X_k is the j'th series in a stage and P_n is the n'th output in that stage:
    
    X_k = P_{k*S+j}
    E_k is from a stage with 2*S series and it is in the j'th series in the stage
    O_k is from a stage with 2*S series and it is in the (S+j)'th series in stage
    Let Q_n be the n'th output of the stage before P.
    E_k = Q_{k*2*S+j}
    O_k = Q_{k*2*S+S+j}

    Also let T_n = exp(-2*pi*i*n/M)
        
    M = N*S (total number of items in stage output)
    P_{k*S+j}     = Q_{2*k*S+j} + T_{k*S} * Q_{k*2*S+S+j}
    P_{k*S+j+M/2} = Q_{2*k*S+j} - T_{k*S} * Q_{k*2*S+S+j}
    
    We'll give these addresses names:
    to_addr0 = k*S+j
    to_addr1 = k*S+j+M/2
    from_addr0 = 2*k*S+j
    from_addr1 = 2*k*S+S+j
    
    Now we assume we know to_addr0 and try to get efficient ways to calculate the
    other addresses.

    to_addr0 = k*S+j   (j ranges from 0 to S-1, and S is a multiple of two)
    If we look at to_addr0 in binary the lowest log2(S) bits give the value of j
    and the highest log2(N) bits give the value for k.
    */
    
   //To get from_addr0 we leave the lowest log2(S) bits alone but we shift the log2(N)
   //highest bits to the left (high is to left).
   
   //To get from_addr1 we add S to from_addr0.

   // to_addr1_bf = out0+addr + M/2
   // We simply flip the highest bit from 0 to 1 which adds M/2.
   assign to_addr1_bf = {1'b1, to_addr0_bf[LOG_N-2:0]};
   // from_addr0 = 2*k*S+j
   // (to_addr0_bf & series_bits) = j
   // (to_addr0_bf & ~series_bits) = k*S
   // Since the bits don't overlap we can add them with an OR.
   assign from_addr0 = (to_addr0_bf & series_bits) | ((to_addr0_bf & ~series_bits)<<1);
   assign from_addr1 = from_addr0 + S;
   // (to_addr0_bf & ~series_bits) = k*S
   assign tf_addr = to_addr0_bf & ~series_bits;

   wire [WIDTH-1:0]         tf;
   reg                      tf_addr_nd;
   
   twiddlefactors_{{N}} twiddlefactors_inst
     (.clk (clk),
      .addr (tf_addr),
      .addr_nd (tf_addr_nd),
      .tf_out (tf)
      );

   reg                      bf_nd;
   reg                      control_error;
   reg                      reading;
   
   butterfly 
     #(.MWIDTH   (2*LOG_N),
	   .WIDTH   (WIDTH)
	   )
   butterfly_0
     (.clk (clk),
	  .rst_n (rst_n),
	  .m_in ({to_addr0_bf, to_addr1_bf}),
	  .w (tf),
	  .xa (from_data0),
	  .xb (from_data1),
	  .x_nd (bf_nd),
	  .m_out ({to_addr0, to_addr1}),
	  .ya (to_data0),
	  .yb (to_data1),
	  .y_nd (to_nd)
	  );

   always @ (posedge clk)
     begin
        // Default values.
        tf_addr_nd <= 1'b0;
        bf_nd <= 1'b0;
        if (~rst_n)
          begin
             mode <= 1'b0;
             active <= 1'b0;
             reading <= 1'b0;
             control_error <= 1'b0;
          end
        else if (start_A | start_B)
          begin
             reading <= 1'b1;
             active <= 1'b1;
             mode <= start_B;
             if (start_A & start_B)
               control_error <= 1'b1;
             if (active | reading)
               control_error <= 1'b1;
		     series_bits <= {LOG_N{1'b1}} >> (stage_index+1);
		     // In stage_index 0 There are N/2 series.
             // There are half as many in each subsequent stage.
		     S <= {1'b1,{LOG_N-1{1'b0}}} >> stage_index;
             to_addr0_bf <= {LOG_N{1'b0}};
             tf_addr_nd <= 1'b1;
          end
        else if (reading)
          begin
             // Send data to the butterfly every second clock cycle.
             bf_nd <= ~bf_nd;
             if (bf_nd)
               begin
                  to_addr0_bf <= to_addr0_bf+1;
                  tf_addr_nd <= 1'b1;
                  if (to_addr0_bf == N/2-1)
                    begin
                       reading <= 1'b0;
                    end
               end
          end
        else if (to_nd & (to_addr0 == N/2-1))
          begin
             if (reading)
               control_error <= 1'b1;
             active <= 1'b0;
          end
     end

   assign error = control_error;
   
endmodule

