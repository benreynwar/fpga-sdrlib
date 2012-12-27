
`ifndef XILINX
  
module MULT18X18S
  // The module was copied from the Ettus UHD code.
  (output reg signed [35:0] P,
   input signed [17:0] A,
   input signed [17:0] B,
   input C,    // Clock
   input CE,   // Clock Enable
   input R     // Synchronous Reset
   );
   
   always @(posedge C)
     if(R)
       P <= 36'sd0;
     else if(CE)
       begin
          P <= A * B;
       end
endmodule 

`endif

module multiply
  #(
    parameter WDTH = 0
    )
   (
    input wire                   clk,
    input wire                   rst_n,
    input wire signed [WDTH-1:0] x,
    input wire signed [WDTH-1:0] y,
    output wire signed [WDTH-1:0] z
    );

   reg                          ce;
   initial
     ce <= 1'b1;
   
   wire signed [17:0]            xb;
   wire signed [17:0]            yb;
   assign xb = x;
   assign yb = y;
   wire signed [35:0]       xy;
   
   MULT18X18S multer (.P(xy), .A(xb), .B(yb), .C(clk), .CE(ce), .R(~rst_n));   

   assign z = xy >>> (WDTH-1);
   
   always @ (posedge clk)
     begin
        //xy <= xb * yb;
        //z <= xy >>> (WDTH-2);
      end
   
endmodule


