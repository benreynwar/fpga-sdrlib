// -*- verilog -*- 
// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module taps
  #(
    parameter N = 0,
    parameter ADDRLEN = 0,
    parameter FLTLEN = 0,
    parameter WDTH = 0
    )
  (
   input wire                   clk,
   input wire [ADDRLEN-1:0]     addr,
   output reg [FLTLEN*WDTH-1:0] outtaps
   );
   
   reg [FLTLEN*WDTH-1:0]         tapvalues[N-1:0];
   
   always @ (posedge clk)
     begin
        case (addr)
        {% for i, taps in channels %}
          {{addrlen}}'d{{i}}: outtaps <= { {% for tap in taps %}{{tap.sign}}{{tap_width}}'sd{{tap.value}}{% if not loop.last %},{% endif %}{% endfor %} };
        {% endfor %}
        endcase
     end
   
endmodule