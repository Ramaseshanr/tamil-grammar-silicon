// tamil_noun_front.sv — the streaming front end of the Tamil noun datapath.
//
// # What this is
// A phoneme stream in, a declension class out. One TLP1 byte per cycle; assert `last` with
// the final phoneme of the stem and the class is valid the cycle after.
//
// # Why the decision is a separate module
// `tamil_noun_class` (generated from hdl/src by RustHDL, the same generator as
// SanskritOS/hdl_synth) is purely combinational: 122 LUT4, no flip-flops. It is the
// *theorem* — audit/DERIVABILITY.md measured that 40 contexts assign the class of 44,076
// stems, a 1,105× compression, so no stem lexicon is needed at all. This module is only
// the small amount of state that theorem needs to see:
//
//   r1, r2, r3   the last three phonemes          (derive_nouns.context reads b[-1..-3])
//   len          stem length, SATURATING at 4     (context tests len>1, len>2, len>=4)
//   uyir         vowel count, SATURATING at 3     (context tests ==1 and >2)
//
// The saturation is not an approximation. Those are every length and count predicate the
// grammar uses, so 3 bits and 2 bits carry the whole rule exactly. A stem of 41 phonemes
// — the longest in the gold — needs no more state than a stem of 4.
//
// # The sentinel subtlety
// r2 and r3 are 0 before enough phonemes have arrived, and 0x00 is also அ. The disambiguator
// is `len`, not the sentinel: every branch that reads r2 is guarded by len>1 and every branch
// that reads r3 by len>2. This mirrors tools/derive_nouns.py exactly, which uses the same
// `b[-2] if len(b) > 1 else 0`. Verified: 0 conflicting assignments over 43,647 stems.
//
// # The reference
// tools/derive_nouns.py is the authority. Where this disagrees with it, this is wrong:
// every figure in audit/ was measured against the Python. hdl/tb/tb_noun_stream.v drives
// the TLP1 encoding of all 43,647 classifiable stems through this module and compares.

module tamil_noun_front (
    input  logic       clk,
    input  logic       rst,       // synchronous, active high: clears the window
    input  logic [7:0] ph,        // TLP1 phoneme
    input  logic       valid,     // ph is a phoneme this cycle
    input  logic       last,      // ...and it is the stem's last
    output logic [4:0] cls,       // declension class
    output logic       ok,        // low if the context is not in the fitted classifier
    output logic       done       // cls/ok are valid this cycle
);
    logic [7:0] r1, r2, r3;
    logic [2:0] len;
    logic [1:0] uyir;

    // TLP1: category is bits 7-6, and 00 is uyir. One mask, one compare.
    wire is_uyir = (ph[7:6] == 2'b00);

    always_ff @(posedge clk) begin
        if (rst) begin
            r1 <= 8'h00; r2 <= 8'h00; r3 <= 8'h00;
            len <= 3'd0; uyir <= 2'd0; done <= 1'b0;
        end else begin
            done <= 1'b0;
            if (valid) begin
                r3 <= r2;
                r2 <= r1;
                r1 <= ph;
                if (len  != 3'd4) len  <= len  + 3'd1;   // saturate at 4
                if (is_uyir && uyir != 2'd3) uyir <= uyir + 2'd1;   // saturate at 3
                if (last) done <= 1'b1;
            end
            // a stem ends where it ends; the next one starts from a cleared window
            if (valid && last) begin
                r1 <= 8'h00; r2 <= 8'h00; r3 <= 8'h00;
                len <= 3'd0; uyir <= 2'd0;
            end
        end
    end

    // The window presented to the decision is the one INCLUDING the phoneme arriving now,
    // so the combinational core sees the complete stem on the `last` cycle and `done`
    // registers its answer one cycle later. Hence the bypasses below.
    wire [7:0] w1 = valid ? ph : r1;
    wire [7:0] w2 = valid ? r1 : r2;
    wire [7:0] w3 = valid ? r2 : r3;
    wire [2:0] wlen  = (valid && len != 3'd4) ? len + 3'd1 : len;
    wire [1:0] wuyir = (valid && is_uyir && uyir != 2'd3) ? uyir + 2'd1 : uyir;

    logic [4:0] cls_c;
    logic       ok_c;
    tamil_noun_class core (
        .p1(w1), .p2(w2), .p3(w3), .len(wlen), .uyir(wuyir),
        .cls(cls_c), .ok(ok_c)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            cls <= 5'd0; ok <= 1'b0;
        end else if (valid && last) begin
            cls <= cls_c;
            ok  <= ok_c;
        end
    end
endmodule
