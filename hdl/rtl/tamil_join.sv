// tamil_join.sv -- the juncture rules of the noun derivation, as combinational logic.
//
// This is tools/phon_rules.py::join(): what happens where a stem meets an ending. It is written
// branch for branch in the same priority order, and every branch carries the verse it comes from.
// The Python is the authority; hdl/tb/tb_join.v drives this module with every combination of the
// valid phonemes and the eight flags, plus a seeded random sample over all 256 byte values, and
// compares with phon_rules.join().
//
// It does not move strings. It says what the seam does:
//     drop_left   the left form loses its last byte
//     ins_v/ins_b one byte is inserted at the seam (the byte is ins_b)
//     drop_right  the right form loses its first byte
// A sequencer (not built yet) applies that to the byte streams.
//
// Inputs: a is the left form's last byte; a2m is 1 when the byte before it is a மெய் (the one fact about
// it the rules use, in P5); b is the right form's first byte; flags are the per-morpheme properties.
`include "gen/tamil_phon.vh"

module tamil_join (
    input  wire [7:0] a,
    input  wire       a2m,
    input  wire [7:0] b,
    input  wire [7:0] flags,        // {pada, gem, clitic, kural, inc, dbl, mono, nohard}
    output reg        drop_left,
    output reg        ins_v,
    output reg  [7:0] ins_b,
    output reg        drop_right
);
    wire pada = flags[7], gem = flags[6], clitic = flags[5], kural = flags[4];
    wire inc  = flags[3], dbl = flags[2], mono   = flags[1], nohard = flags[0];

    // TLP1 predicates: each is one mask and one compare (spec/TLP1.md)
    wire a_v   = (a[7:6] == 2'b00);          // உயிர்
    wire b_v   = (b[7:6] == 2'b00);
    wire a_mey = (a[7:6] == 2'b01);          // மெய்
    wire b_val = (b[7:4] == 4'h4);           // வல்லினம்: மெய், இனம் 00
    wire a_mel = (a[7:4] == 4'h5);           // மெல்லினம்: மெய், இனம் 01
    wire b_pada = (b == `CA) || (b == `TTA) || (b == `THA) || (b == `PA);   // the only triggers at a word boundary
    wire front = a[0] && (a[2:0] != 3'b111); // vowel quality i, e, ai (1, 3, 5) takes ய்; the rest take வ்
    wire hard_a = (a == `LA) || (a == `LLA) || (a == `NA);

    always @* begin
        drop_left = 1'b0; ins_v = 1'b0; ins_b = 8'h00; drop_right = 1'b0;
        if (clitic) begin
            // P10  a particle doubles its initial வல்லினம் after a vowel; no புணரியல் otherwise
            if (dbl && b_val && a_v) begin ins_v = 1'b1; ins_b = b; end
        end else if (inc && a_v && (a == b)) begin
            // P9  coalescence: two identical vowels become one (மர + அத்து -> மரத்து)  [Naṉṉūl 244]
            drop_right = 1'b1;
        end else if (pada && !b_pada) begin
            // at a pada juncture only ச் ட் த் ப் trigger anything
        end else if (kural && (a == `U) && b_v && a2m) begin
            // P5  hiatus: a குற்றியலுகரம் drops before a vowel  [Naṉṉūl 164: உயிர்வரின் உக்குறள் மெய்விட்டு ஓடும்]
            drop_left = 1'b1;
        end else if (a_v && b_v) begin
            // P6  உடம்படுமெய்: a glide fills a vowel-vowel seam, ய் after i e ai, otherwise வ்
            ins_v = 1'b1; ins_b = front ? `YA : `VA;
        end else if (pada && a_mel) begin
            // P3  nasal loss at a pada juncture
            drop_left = 1'b1;
        end else if ((a == `MA) && b_val && !pada) begin
            // P1  assimilation: ம் takes the place of a following வல்லினம்  [Tolkāppiyam பிறப்பியல் 7-9]
            //     (a & ~7) | (b & 7): two masks and an OR
            drop_left = 1'b1; ins_v = 1'b1; ins_b = (a & 8'hF8) | (b & 8'h07);
        end else if (hard_a && b_val && !pada && !nohard) begin
            // P2  hardening: ல் ள் ன் before a வல்லினம்  [Naṉṉūl 227]
            //     (a & 7) | 0x40: the place bits kept, the hard-consonant class supplied
            drop_left = 1'b1; ins_v = 1'b1; ins_b = (a & 8'h07) | 8'h40;
        end else if (mono && a_mey && b_v) begin
            // P11  ஒற்று இரட்டல்: the final ஒற்று doubles before a vowel உருபு (monosyllables)
            ins_v = 1'b1; ins_b = a;
        end else if (a_v && b_val && gem && !pada) begin
            // P4  வல்லினம் மிகல்: the suffix-initial வல்லினம் doubles after a vowel
            ins_v = 1'b1; ins_b = b;
        end
    end
endmodule
