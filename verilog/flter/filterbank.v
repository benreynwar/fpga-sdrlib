// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module filterbank
  #(
    parameter N = 8,
    parameter WIDTH = 32,
    parameter MWIDTH = 1,
    parameter FLTLEN = 10,
    parameter ID = 0,
    parameter MSG_BUFFER_LENGTH = 64
    )
   (
    input wire                   clk,
    input wire                   rst_n,
    input wire [WIDTH-1:0]       in_data,
    input wire                   in_nd,
    input wire [MWIDTH-1:0]      in_m,
    // Takes input messages to set taps.
    input wire [`MSG_WIDTH-1:0]  in_msg,
    input wire                   in_msg_nd, 
    output wire [WIDTH-1:0]      out_data,
    output wire                  out_nd,
    output wire [MWIDTH-1:0]     out_m,
    output wire [`MSG_WIDTH-1:0] out_msg,
    output wire                  out_msg_nd, 
    output wire                  first_filter,
    output wire                  error
    );
   
   function integer clog2;
      input integer             value;
      begin
         value = value-1;
         for (clog2=0; value>0; clog2=clog2+1)
           value = value>>1;
      end
   endfunction
   
   localparam integer           LOG_N = clog2(N);
   localparam integer           LOG_FLTLEN = clog2(FLTLEN);
   
   wire [N-1:0]                 in_nds;
   reg [N-1:0]                  in_nds_mask;
   wire [WIDTH-1:0]             out_datas[N-1:0];
   reg [LOG_N-1:0]              out_filter;
   wire [N-1:0]                 out_nds;
   wire [N-1:0]                 out_filter_unexpected;                 
   wire                         out_filter_unexpected_error;

   assign in_nds = in_nds_mask & {N{in_nd}};
   assign out_nd = out_nds[out_filter];
   assign out_data = out_datas[out_filter];
   assign out_filter_unexpected_error = | out_filter_unexpected;

   reg [`MSG_WIDTH-1:0]         in_filter_msg;
   reg                          in_filter_msg_nd;
   wire [N-1:0]                 filter_errors;
   wire                         filter_error;

   assign filter_error = |filter_errors;
   
   genvar                       i;
   generate
      for (i=0; i<N; i=i+1) begin: loop_0

         // We got new data from a filter and weren't expecting it.
         assign out_filter_unexpected[i] = ((i!=out_filter) & (out_nds[i]))?1'b1:1'b0;
         
         reg                   in_m;
         wire                  out_m;
         wire [`MSG_WIDTH-1:0] out_filter_msg;
         wire                  out_filter_msg_nd;
         
         filter #(WIDTH, MWIDTH, FLTLEN, i) filter_0
             (.clk(clk),
              .rst_n(rst_n),
              .in_data(in_data),
              .in_nd(in_nds[i]),
              .in_m(in_m),
              .in_msg(in_filter_msg),
              .in_msg_nd(in_filter_msg_nd),
              .out_data(out_datas[i]),
              .out_nd(out_nds[i]),
              .out_m(out_m),
              .out_msg(out_filter_msg),
              .out_msg_nd(out_filter_msg_nd),
              .error(filter_errors[i])
              );
      end
   endgenerate
        
   wire                        buffer_error;
   wire [WIDTH-1:0]            read_msg;
   wire                        read_msg_ready;
   reg                         delete_msg;
   
   buffer_BB #(WIDTH, MSG_BUFFER_LENGTH) buffer_BB_0
     (.clk(clk),
      .rst_n(rst_n),
      .write_strobe(in_msg_nd),
      .write_data(in_msg),
      .read_delete(delete_msg),
      .read_full(read_msg_ready),
      .read_data(read_msg),
      .error(buffer_error)
      );

   localparam N_LENGTH = 10;
   reg [N_LENGTH-1:0]          which_filter;
   // which_pos is one bit longer then we would expect.
   // We use this to indicate a header is to be sent.
   reg [LOG_FLTLEN:0]        which_pos;
   reg                         setting_taps;
   reg [`MSG_WIDTH-1:0]        filter_msg_header;
   reg [`MSG_LENGTH_WIDTH-1:0] msg_length;
   reg                         tap_set_error;

   // Read from the msg buffer and forward messages on to filter modules.
   always @ (posedge clk)
     if (~rst_n)
       begin
        setting_taps <= 1'b0;
        tap_set_error <= 1'b0;
        msg_length <= FLTLEN;
       end
     else if (read_msg_ready)
       begin
          // If first bit is 1 then this is a header so we start reseting taps.
          if (read_msg[`MSG_WIDTH-1])
            begin
               // FIXME: Check that length is correct.
               // FIXME: Check that ID is correct.
               which_filter <= {N_LENGTH{1'b0}};
               // Now send a header to the first filter.
               which_pos <= {LOG_FLTLEN{1'b0}};
               setting_taps <= 1'b1;
               in_filter_msg <= {1'b1, msg_length, 4'b0, {N_LENGTH{1'b0}}, 7'b0};
               // Delete the received header from the buffer.
               delete_msg <= 1'b1;
               in_filter_msg_nd <= 1'b1;
               // We tried to set taps while being in the middle of setting them.
               if (setting_taps)
                 begin
                    tap_set_error <= 1'b1;
                 end
            end
          else if (setting_taps)
            begin
               in_filter_msg_nd <= 1'b1;
               if (which_pos == FLTLEN)
                 begin
                    // We finished sending the taps for the previous filter.
                    // Send out a header for the next filter.
                    // `which_filter` has already been updated.
                    in_filter_msg <= {1'b1, msg_length, 4'b0, which_filter, 7'b0};
                    which_pos <= {LOG_FLTLEN{1'b0}};
                    delete_msg <= 1'b0;
                 end
               else
                 begin
                    which_pos <= which_pos + 1;
                    in_filter_msg <= read_msg;
                    delete_msg <= 1'b1;
                    if (which_pos == FLTLEN-1)
                      begin
                         if (which_filter == N-1)
                           // If this is the last tap of the last filter we are finished.
                           begin
                              setting_taps <= 1'b0;
                           end
                         else
                           // If there is another filter then update `which_filter` so
                           // we send the header to the right place.
                           begin
                              which_pos <= which_pos + 1;
                              which_filter <= which_filter + 1;
                           end
                      end
                 end
            end
          else
            begin
               // A message is there but it's not a header and we're
               // not setting taps so just delete it.
               delete_msg <= 1'b1;
            end // else: !if(setting_taps)
       end
     else
       begin
          // No message ready.
          // Not setting any taps.
          in_filter_msg_nd <= 1'b0;
          // Not reading any taps.
          delete_msg <= 1'b0;
       end

   // Pass the input stream to the filters.
   always @ (posedge clk)
     begin
        if (~rst_n)
          begin
             in_nds_mask <= {{N-1{1'b0}}, 1'b1};
          end
        else if (in_nd)
          begin
             if (in_nds_mask[N-1])
               in_nds_mask <= {{N-1{1'b0}}, 1'b1};
             else
               in_nds_mask <= in_nds_mask << 1;
          end
     end

   // Get the output stream from the filters.
   always @ (posedge clk)
     if (~rst_n)
       out_filter <= {LOG_N{1'b0}};
     else if (out_nd)
       if (out_filter == N-1)
         out_filter <= {LOG_N{1'b0}};
       else
         out_filter <= out_filter + 1;

   always @ (posedge clk)
     begin
        //if (error)
        //  $display("%d %d %d %d %d", out_filter_unexpected_error, buffer_write_error, buffer_read_error, tap_set_error, filter_error);
        //$display("out_filter=%d in_nds=%b out_nds=%b", out_filter, in_nds, out_nds);
     end
   assign error = out_filter_unexpected_error | buffer_error | tap_set_error | filter_error;

endmodule 