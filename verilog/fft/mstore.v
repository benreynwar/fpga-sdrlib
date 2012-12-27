module mstore
  #(
    parameter N = 0,
    parameter MWIDTH = 1
    )
   (
    input wire               clk,
    input wire               rst_n,
    input wire               in_nd,
    input wire [MWIDTH-1:0]  in_m,
    input wire               in_read,
    output wire [MWIDTH-1:0] out_m,
    output reg               error
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

   reg [LOG_N-1:0]               addr;
   wire [LOG_N-1:0]               next_addr;
   reg [MWIDTH-1:0]              RAM[N-1:0];
   reg                           filling;

   assign next_addr = addr+1;
   assign out_m = (in_read)?RAM[next_addr]:RAM[addr];
   
   always @ (posedge clk)
     if (~rst_n)
       begin
          addr <= {LOG_N{1'b0}};
          error <= 1'b0;
          filling <= 1'b1;
       end
     else
       begin
          // If we have new data make sure we're in the filling
          // state and write the data.
          if (in_nd)
            if (~filling)
              error <= 1'b1;
            else
              RAM[addr] <= in_m;
          // If a value has been read make sure we're not in the
          // filling state.
          else if (in_read)
            if (filling)
              error <= 1'b1;
          // If we have new data or data has been read then we
          // increment the position.
          if (in_nd | in_read)
            if (addr == N-1)
              begin
                 addr <= {LOG_N{1'b0}};
                 filling <= ~filling;
              end
            else
              addr <= addr + 1;
       end
         
endmodule
