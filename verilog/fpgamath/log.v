// Taken from:
// http://www.beyond-circuits.com/wordpress/2008/11/constant-functions/

function integer log2;
   input integer value;
   begin
      value = value-1;
      for (log2=0; value>0; log2=log2+1)
        value = value>>1;
   end
endfunction
