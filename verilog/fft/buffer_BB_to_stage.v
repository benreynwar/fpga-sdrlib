// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// Connects a buffer_BB to a stage and an mstore and takes care of
// transfering data.

module buffer_BB_to_stage
 #(
   parameter N = 8,
   parameter LOG_N = 3,
   parameter WIDTH = 32,
   parameter MWIDTH = 1
   )
   (
    input wire                     clk,
    input wire                     rst_n,
    // Start signals
    input wire                     start,
    // From buffer_BB
    input wire                     read_full,
    input wire [WIDTH+MWIDTH-1: 0] read_data,
    output reg                     read_delete,
    // To Stage
    output wire [LOG_N-1:0]        out_addr0,
    output wire [LOG_N-1:0]        out_addr1,
    output reg                     out_nd,
    output reg [WIDTH-1:0]         out_data0,
    output reg [WIDTH-1:0]         out_data1,
    // To mStore
    output reg                     out_mnd,
    output reg [MWIDTH-1:0]        out_m,
    // Finished Signal
    output reg                     finished,
    output reg                     error
    );

   reg                             active;
   reg [LOG_N-1:0]                 addr;
   assign out_addr0 = addr;
   assign out_addr1 = addr + 1;
   reg                             read_counter;
   wire [WIDTH-1:0]                read_data_s;
   wire [MWIDTH-1:0]               read_data_m;
   assign {read_data_s, read_data_m} = read_data;
   reg                             first_read;
   
   always @ (posedge clk)
     begin
        // Set the default values;
        out_nd <= 1'b0;
        finished <= 1'b0;
        read_delete <= 1'b0;
        out_mnd <= 1'b0;
        if (~rst_n)
          begin
             active <= 1'b0;
             addr <= {LOG_N{1'b0}};
             read_counter <= 1'b0;
             error <= 1'b0;
          end
        else if (start)
          begin
             if (active)
               error <= 1'b1;
             else
               begin
                  active <= 1'b1;
                  addr <= {LOG_N{1'b0}};
                  read_counter <= 1'b0;
                  first_read <= 1'b1;
               end
          end
        else if (active & read_full)
          begin
             out_mnd <= 1'b1;
             out_m <= read_data_m;
             // We can only read one item from the buffer each block
             // cycle.  But we write to the stage two at a time
             // so we have to save values and only write every second
             // clock cycle.
             read_counter <= ~read_counter;
             read_delete <= 1'b1;
             if (~read_counter)
               begin
                  out_data0 <= read_data_s;
                  if (~first_read)
                    addr <= addr + 2;
                  first_read <= 1'b0;
               end
             else
               begin
                  out_data1 <= read_data_s;
                  out_nd <= 1'b1;
                  if (addr == N-2)
                    begin
                       active <= 1'b0;
                       finished <= 1'b1;
                    end
               end
          end
     end
endmodule