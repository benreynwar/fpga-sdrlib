// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module filterbank_ccf
  #(
    parameter N = 8,
    parameter ADDRLEN = 3,
    parameter WDTH = 32,
    parameter MWDTH = 1,
    parameter FLTLEN = 10
    )
   (
    input wire              clk,
    input wire              rst_n,
    input wire [WDTH-1:0]   in_data,
    input wire              in_nd,
    input wire [MWDTH-1:0]  in_m,
    
    output wire [WDTH-1:0]  out_data,
    output wire             out_nd,
    output wire [MWDTH-1:0] out_m,
    output wire             first_filter,
    output wire             error
    );
   
   reg [WDTH*(FLTLEN-1)-1:0] histories[N-1:0];
   reg [ADDRLEN-1:0]         filter_n;
   wire [WDTH*(FLTLEN-1)-1:0] mult_histories;
   wire [WDTH/2*FLTLEN-1:0]   mult_taps;
   wire                       in_first_filter;
   assign mult_histories = histories[filter_n];
   assign in_first_filter = (~|filter_n);

   initial
     begin
        filter_n <= {ADDRLEN{1'b0}};
        {{zerohistories}}
     end
   always @ (posedge clk or negedge rst_n)
     begin
        if (~rst_n)
          begin
             filter_n <= {ADDRLEN{1'b0}};
             {{zerohistories}}
          end
        else
          begin
             if (in_nd)
               begin
                  if (filter_n == N-1)
                    filter_n <= {ADDRLEN{1'b0}};
                  else
                    filter_n <= filter_n + 1;
                  {{shifthistories}}
                  histories[filter_n][WDTH-1 -:WDTH] <= in_data;
               end
          end
     end

   taps #(N, ADDRLEN, FLTLEN, WDTH/2) taps_i
     (.addr(filter_n),
      .outtaps(mult_taps)
     );

   summult #(WDTH/2, MWDTH+1, FLTLEN) summult_i
     (.clk(clk),
      .rst_n(rst_n),
      .in_nd(in_nd),
      .in_m({in_m, in_first_filter}),
      .in_xs({mult_histories, in_data}),
      .in_ys(mult_taps),
      .out_data(out_data),
      .out_nd(out_nd),
      .out_m({out_m, first_filter}),
      .overflow(error)
      );

endmodule