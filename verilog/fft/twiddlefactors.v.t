// Copyright (c) 2012 Ben Reynwar
// Released under MIT License (see LICENSE.txt)

module twiddlefactors_{{N}} (
    input  wire                            clk,
    input  wire [{{log_N - 2}}:0]          addr,
    input  wire                            addr_nd,
    output reg signed [{{2*tf_width-1}}:0] tf_out
  );

  always @ (posedge clk)
    begin
      if (addr_nd)
        begin
          case (addr)
			{% for tf in tfs %}
            {{log_N-1}}'d{{tf.i}}: tf_out <= { {{tf.re_sign}}{{tf_width}}'sd{{tf.re}},  {{tf.im_sign}}{{tf_width}}'sd{{tf.im}} };
			{% endfor %}
            default:
              begin
                tf_out <= {{2*tf_width}}'d0;
              end
         endcase
      end
  end
endmodule
