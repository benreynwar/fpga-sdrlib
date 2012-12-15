// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// A qa_wrapper with a buffer_AA.

module qa_wrapper
  #(
    parameter WDTH = 32
    )
   (
    input wire            clk,
    input wire            reset,
    input wire [WDTH-1:0] in_data,
    input wire            in_nd,
    output reg [WDTH-1:0] out_data,
    output reg            out_nd
    );

   wire                    rst_n;
   assign rst_n = ~reset;
   reg                     read_delete;
   wire                    read_full;
   wire [WDTH-1:0]         read_data;
   wire                    write_error;
   wire                    read_error;
   wire [`BUFFER_LENGTH-1:0] full;
   reg [`LOG_BURST_LENGTH-1:0] burst_counter;

   buffer_AA #(WDTH, `BUFFER_LENGTH, `LOG_BUFFER_LENGTH)
   the_buffer 
     (.clk(clk),
      .rst_n(rst_n),
      .write_strobe(in_nd),
      .write_data(in_data),
      .read_delete(read_delete),
      .read_full(read_full),
      .read_data(read_data),
      .write_error(write_error),
      .read_error(read_error),
      .full(full)
      );

   always @ (posedge clk)
     begin
        if (!rst_n)
          begin
             read_delete <= 1'b0;
             out_data <= {WDTH{1'b0}};
             out_nd <= 1'b0;
             burst_counter <= {`LOG_BURST_LENGTH{1'b0}};
          end
        else
          if (write_error)
            begin
               out_nd <= 1'b1;
               out_data <= `WRITEERRORCODE;
               read_delete <= 1'b0;
            end
          else if (read_error)
            begin
               out_nd <= 1'b1;
               out_data <= `READERRORCODE;
               read_delete <= 1'b0;
            end
          else
            begin
               if (!read_delete && read_full && !(|burst_counter))
                 begin
                    read_delete <= 1'b1;
                    out_nd <= 1'b1;
                    out_data <= read_data;
                 end
               else
                 begin
                    if (!read_delete && in_nd)
                      burst_counter <= burst_counter + 1;
                    read_delete <= 1'b0;
                    out_nd <= 1'b0;
                 end
            end
     end
   
endmodule