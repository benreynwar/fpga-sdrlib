// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// This module updates the read_data immediately upon getting
// a delete signal (using assign).

module buffer_BB
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
    output wire                read_full,
    output wire [WIDTH-1: 0]   read_data,
    // Buffer overflow.
    output reg                write_error,
    output reg                read_error
    );

   reg [MEM_SIZE-1:0]         full;
   reg [WIDTH-1: 0]           RAM[MEM_SIZE-1:0];
   reg [LOG_MEM_SIZE-1: 0]    write_addr;
   reg [LOG_MEM_SIZE-1: 0]    read_addr0;
   reg                        read_full0;
   reg                        read_full1;
   reg [WIDTH-1:0]            read_data0;
   reg [WIDTH-1:0]            read_data1;
   wire [LOG_MEM_SIZE-1: 0]   read_addr1;
   wire [LOG_MEM_SIZE-1: 0]   read_addr2;

   assign read_addr1 = read_addr0 + 1;
   assign read_addr2 = read_addr0 + 2;

   assign read_full = (read_delete)?read_full1:read_full0;
   assign read_data = (read_delete)?read_data1:read_data0;
   
   always @(posedge clk)
     if (!rst_n)
       begin
          write_error <= 1'b0;
          read_error <= 1'b0;
          full <= {MEM_SIZE{1'b0}};
          write_addr <= {LOG_MEM_SIZE{1'b0}};
          read_addr0 <= {LOG_MEM_SIZE{1'b0}};
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
               if (full[read_addr0])
                 begin
                    full[read_addr0] <= 1'b0;
                    read_addr0 <= read_addr1;
                    read_full0 <= full[read_addr1];
                    read_data0 <= RAM[read_addr1];
                    read_full1 <= full[read_addr2];
                    read_data1 <= RAM[read_addr2];
                 end
               else
                 begin
                    read_error <= 1'b1;
                    read_full0 <= full[read_addr0];
                    read_data0 <= RAM[read_addr0];
                    read_full1 <= full[read_addr1];
                    read_data1 <= RAM[read_addr1];
                 end
            end
          else
            begin
               read_full0 <= full[read_addr0];
               read_data0 <= RAM[read_addr0];
               read_full1 <= full[read_addr1];
               read_data1 <= RAM[read_addr1];
            end
       end
endmodule

