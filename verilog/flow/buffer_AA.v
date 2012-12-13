// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// The suffix _AA is meaningless.

module buffer_AA
  #(
    parameter WIDTH = 32,
    parameter MEM_SIZE = 64,
    parameter LOG_MEM_SIZE = 6
    )
   (
    input wire                clk,
    input wire                rst_n,
    // Write new data.
    input wire                write_strobe,
    input wire [WIDTH-1: 0]   write_data,
    // Delete the current read data.
    input wire                read_delete,
    // The current read data.
    output reg                read_full,
    output reg [WIDTH-1: 0]   read_data,
    // Buffer overflow.
    output reg                write_error,
    output reg                read_error,
    // Which are full (for debugging)
    output reg [MEM_SIZE-1:0] full
    );
   
   reg [WIDTH-1: 0]           RAM[MEM_SIZE-1:0];
   //reg [MEM_SIZE-1: 0]        full;
   reg [LOG_MEM_SIZE-1: 0]    write_addr;
   reg [LOG_MEM_SIZE-1: 0]    read_addr;
   wire [LOG_MEM_SIZE-1: 0]    next_read_addr;

   assign next_read_addr = read_addr + 1;
   
   always @(posedge clk)
     if (!rst_n)
       begin
          write_error <= 1'b0;
          read_error <= 1'b0;
          full <= {MEM_SIZE{1'b0}};
          write_addr <= {LOG_MEM_SIZE{1'b0}};
          read_addr <= {LOG_MEM_SIZE{1'b0}};
       end
     else
       begin
          if (write_strobe)
            begin
               if (!full[write_addr])
                 begin
                    RAM[write_addr] <= write_data;
                    full[write_addr] <= 1'b1;
                    write_addr <= write_addr + 1;
                 end
               else
                 write_error <= 1'b1;
            end
          if (read_delete)
            begin
               if (full[read_addr])
                 begin
                    full[read_addr] <= 1'b0;
                    read_addr <= next_read_addr;
                    read_full <= full[next_read_addr];
                    read_data <= RAM[next_read_addr];
                 end
               else
                 begin
                    read_error <= 1'b1;
                    read_full <= full[read_addr];
                    read_data <= RAM[read_addr];
                 end
            end
          else
            begin
               read_full <= full[read_addr];
               read_data <= RAM[read_addr];
            end
       end
endmodule

