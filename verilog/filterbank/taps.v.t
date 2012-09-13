// -*- verilog -*- 
module taps
  #(
    parameter N = 0,
    parameter ADDRLEN = 0,
    parameter FLTLEN = 0,
    parameter WDTH = 0
    )
  (
   input wire [ADDRLEN-1:0] addr,
   output wire [FLTLEN*WDTH-1:0] outtaps
   );
   
   reg [FLTLEN*WDTH-1:0]         tapvalues[N-1:0];
   
   assign outtaps = tapvalues[addr];

   initial
     begin
        {% for channel in channels %}{% for tap in channel.taps %}tapvalues[{{channel.i}}][(1+{{tap.i}})*WDTH-1 -:WDTH] <= {{tap.sign}}{{tap_width}}'sd{{tap.value}};
        {% endfor%}
        {% endfor %}    
     end

endmodule