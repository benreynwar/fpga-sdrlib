// -*- verilog -*-
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

// Sends out a stream of specified data.
// Useful for doing QA on the FPGA.

module data_source
  #(
    // How often to send a data piece
    parameter SENDNTH = 2,
    // width of the sendnth counter
    parameter LOGSENDNTH = 1,
    // width of a data piece
    parameter WIDTH = 32,
    // width of a meta data piece
    parameter MWIDTH = 1,
    // number of data pieces
    parameter N_DATA = 1,
    // width of the address of a data piece
    parameter LOGNDATA = 1
    )
   (
    input                   clk,
    input                   rst_n,
    output reg              out_nd,
    output reg [WIDTH-1:0]  out_data,
    output reg [MWIDTH-1:0] out_m,
    // error is never set high currently
    output reg              error,
    output reg             first
    );
   
   reg [WIDTH-1:0]      data[N_DATA-1:0];
   reg [MWIDTH-1:0]     ms[N_DATA-1:0];
   reg [LOGNDATA-1:0]   datapos;
   reg [LOGSENDNTH-1:0] sendnthpos; 

   initial
     begin
        datapos <= {LOGNDATA {1'b0}};
        sendnthpos <= {LOGSENDNTH {1'b0}};
        error <= 1'b0;
     end

   always @ (posedge clk)
     begin
        if (~rst_n)
          begin
             datapos <= {LOGNDATA {1'b0}};
             sendnthpos <= {LOGSENDNTH {1'b0}};
             error <= 1'b0;
          end
        else
          begin
             if (sendnthpos == SENDNTH-1)
               sendnthpos <= {LOGSENDNTH {1'b0}};
             else
               sendnthpos <= sendnthpos + 1;
             if (|sendnthpos)
               out_nd <= 1'b0;
             else
               begin
                  // Sending some data.
                  out_nd <= 1'b1;
                  case (datapos)
                    {% for i, d, m in combined %}
                      {{logndata}}'d{{i}}:
                      begin
                        out_data <= { {{d.re_sign}}{{width}}'sd{{d.re}},  {{d.im_sign}}{{width}}'sd{{d.im}} };
                        out_m <= {{mwidth}}'d{{m}};
                      end
			        {% endfor %}
                    default:
                      begin
                         out_data <= {WIDTH {1'b0}};
                         out_m <= 1'b0;
                      end
                    endcase
                  first <= ~|datapos;
                  if (datapos == N_DATA-1)
                    datapos <= {LOGNDATA {1'b0}};
                  else
                    datapos <= datapos + 1;
               end
         end
     end
   
endmodule