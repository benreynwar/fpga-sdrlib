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
    // Number of loops of the data to send
    // N_LOOPS == 0 means infinite loops
    parameter N_LOOPS = 1,
    // width of the address of loop number
    parameter LOGNLOOPS = 1,
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
    output reg              error
    );
   
   reg [WIDTH-1:0]      data[N_DATA-1:0];
   reg [MWIDTH-1:0]     ms[N_DATA-1:0];
   reg [LOGNDATA-1:0]   datapos;
   reg [LOGSENDNTH-1:0] sendnthpos; 
   reg [LOGNLOOPS-1:0] looppos;
   reg                   finished;
   
   initial
     begin
        {% for d in data %}
         data[{{d.i}}] <= { {{d.re_sign}}{{width}}'sd{{d.re}}, {{d.im_sign}}{{width}}'sd{{d.im}} };
        {% endfor %}
        {% for m in ms %}
          ms[{{m.i}}] <= {{m.sign}}{{mwidth}}'sd{{m.value}};
        {% endfor %}
        datapos <= {WIDTH {1'b0}};
        sendnthpos <= {LOGSENDNTH {1'b0}};
        looppos <= {LOGNLOOPS {1'b0}};
        finished <= 1'b0;
        error <= 1'b0;
     end

   always @ (posedge clk or negedge rst_n)
     begin
        if (~rst_n)
          begin
             datapos <= {WIDTH {1'b0}};
             sendnthpos <= {LOGSENDNTH {1'b0}};
             looppos <= {LOGNLOOPS {1'b0}};
             finished <= 1'b0;
             error <= 1'b0;
          end
        else
          begin
             if (~finished)
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
                       out_data <= data[datapos];
                       out_m <= ms[datapos];
                       if (datapos == N_DATA-1)
                         begin
                            // Sent last data piece.
                            // Should we loop again?
                            datapos <= {WIDTH {1'b0}};
                            if ((N_LOOPS > 0) & ((looppos+1==N_LOOPS) | ~|looppos))
                              begin
                                 finished <= 1'b1;
                              end
                            else
                              looppos <= looppos + 1;
                         end
                       else
                         datapos <= datapos + 1;
                    end
               end
             else
               out_nd <= 1'b0;
          end
     end
     
endmodule