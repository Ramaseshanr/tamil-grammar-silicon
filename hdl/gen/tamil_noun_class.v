// GENERATED from hdl/src/{main,classify_gen}.rs by `cargo run` in hdl/.
// Do not edit: regenerate with `python3 tools/gen_hdl.py && cargo run`.
// The authority is tools/derive_nouns.py; hdl/tb checks this against it.


module tamil_noun_class(p1,p2,p3,len,uyir,cls,ok);
    
    // Module arguments
    input wire  [7:0] p1;
    input wire  [7:0] p2;
    input wire  [7:0] p3;
    input wire  [2:0] len;
    input wire  [1:0] uyir;
    output reg  [4:0] cls;
    output reg  ok;
    
    // Update code
    always @(*) begin
        cls = 64'h0;
        ok = 1'b0;
        if ((len > 64'h2) & (p1 == 64'h2) & ((p2 == 64'h42) | (p2 == 64'h45)) & ~((len >= 64'h4) & (p3 == p2))) begin
            ok = 1'b1;
            if ((p3 & 64'hc0) == 64'h40) begin
                cls = 64'he;
            end
            else if (((p3 & 64'hc0) == 64'h0) & ((p3 & 64'h8) == 64'h8)) begin
                if (p2 == 64'h42) begin
                    cls = 64'h10;
                end
                else begin
                    cls = 64'hf;
                end
            end
            else if (uyir > 64'h2) begin
                if (p2 == 64'h42) begin
                    cls = 64'h10;
                end
                else begin
                    cls = 64'hf;
                end
            end
            else begin
                cls = 64'h11;
            end
        end
        else if ((p1 == 64'h55) & (len > 64'h1)) begin
            ok = 1'b1;
            if ((p2 == 64'h0) & (uyir == 64'h1)) begin
                cls = 64'h2;
            end
            else begin
                cls = 64'h3;
            end
        end
        else if ((p1 == 64'h2) & (len > 64'h2)) begin
            if ((p3 & 64'hc0) == 64'h0) begin
                if (p2 == 64'h40) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h41) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h43) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h44) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h52) begin
                    cls = 64'h1;
                    ok = 1'b1;
                end
                else if (p2 == 64'h55) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h60) begin
                    cls = 64'h1;
                    ok = 1'b1;
                end
                else if (p2 == 64'h61) begin
                    cls = 64'h1;
                    ok = 1'b1;
                end
                else if (p2 == 64'h63) begin
                    cls = 64'h1;
                    ok = 1'b1;
                end
                else if (p2 == 64'h64) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h65) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
            end
            else begin
                if (p2 == 64'h40) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h41) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h42) begin
                    cls = 64'ha;
                    ok = 1'b1;
                end
                else if (p2 == 64'h43) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h44) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h45) begin
                    cls = 64'hc;
                    ok = 1'b1;
                end
                else if (p2 == 64'h52) begin
                    cls = 64'h1;
                    ok = 1'b1;
                end
                else if (p2 == 64'h62) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h64) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
                else if (p2 == 64'h65) begin
                    cls = 64'hb;
                    ok = 1'b1;
                end
            end
        end
        else if ((p1 == 64'h2) & (len > 64'h1)) begin
        end
        else begin
            if (p1 == 64'h0) begin
                cls = 64'h7;
                ok = 1'b1;
            end
            else if (p1 == 64'h1) begin
                cls = 64'h7;
                ok = 1'b1;
            end
            else if (p1 == 64'h8) begin
                cls = 64'h1;
                ok = 1'b1;
            end
            else if (p1 == 64'h9) begin
                cls = 64'h8;
                ok = 1'b1;
            end
            else if (p1 == 64'ha) begin
                cls = 64'h1;
                ok = 1'b1;
            end
            else if (p1 == 64'hc) begin
                cls = 64'h1;
                ok = 1'b1;
            end
            else if (p1 == 64'hd) begin
                cls = 64'h7;
                ok = 1'b1;
            end
            else if (p1 == 64'h41) begin
                cls = 64'h7;
                ok = 1'b1;
            end
            else if (p1 == 64'h52) begin
                cls = 64'hd;
                ok = 1'b1;
            end
            else if (p1 == 64'h54) begin
                cls = 64'h5;
                ok = 1'b1;
            end
            else if (p1 == 64'h60) begin
                cls = 64'h9;
                ok = 1'b1;
            end
            else if (p1 == 64'h61) begin
                cls = 64'h9;
                ok = 1'b1;
            end
            else if (p1 == 64'h62) begin
                cls = 64'h4;
                ok = 1'b1;
            end
            else if (p1 == 64'h63) begin
                cls = 64'h6;
                ok = 1'b1;
            end
            else if (p1 == 64'h65) begin
                cls = 64'h9;
                ok = 1'b1;
            end
            else if (p1 == 64'h90) begin
                cls = 64'h3;
                ok = 1'b1;
            end
        end
    end
    
endmodule // tamil_noun_class
