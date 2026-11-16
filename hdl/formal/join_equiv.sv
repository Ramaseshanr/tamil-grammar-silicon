// join_equiv.sv -- the formal checks on tamil_join.sv, over EVERY input (26 free bits: a, a2m, b, flags).
//
//   1. equivalence   tamil_join.sv gives the same four outputs as the flat specification join_spec.sv
//   2. the verses    each rule's statement, written as a property of the RTL's outputs
//   3. hygiene       what the rules never do
//
// Run with hdl/formal/join.sby (SymbiYosys, Yosys, an SMT solver).
`include "gen/tamil_phon.vh"

module join_equiv (
    input  wire [7:0] a,
    input  wire       a2m,
    input  wire [7:0] b,
    input  wire [8:0] flags
);
    wire dl, iv, dr, rv; wire [7:0] ib, rb;
    wire sdl, siv, sdr, srv; wire [7:0] sib, srb;
    tamil_join dut  (.a(a), .a2m(a2m), .b(b), .flags(flags), .drop_left(dl),  .ins_v(iv),  .ins_b(ib),  .drop_right(dr),  .rep_v(rv),  .rep_b(rb));
    join_spec  spec (.a(a), .a2m(a2m), .b(b), .flags(flags), .drop_left(sdl), .ins_v(siv), .ins_b(sib), .drop_right(sdr), .rep_v(srv), .rep_b(srb));

    wire verb = flags[8], pada = flags[7], gem = flags[6], clitic = flags[5], kural = flags[4], inc = flags[3];
    wire a_v = (a[7:6] == 2'b00), b_v = (b[7:6] == 2'b00);
    wire b_pada = (b == `CA) || (b == `TTA) || (b == `THA) || (b == `PA);
    wire front = a[0] && (a[2:0] != 3'b111);

    always @* begin
        // 1. the two statements of the rules agree
        assert (dl == sdl);
        assert (iv == siv);
        assert (ib == sib);
        assert (dr == sdr);
        assert (rv == srv);
        assert (rb == srb);

        // 2. the verses
        // Naṉṉūl 164 (உயிர்வரின் உக்குறள் மெய்விட்டு ஓடும்): a short உ after a consonant drops before a vowel
        if (!clitic && !inc && !(pada && !b_pada) && kural && a == `U && b_v && a2m)
            assert (dl && !iv && !dr);
        // Naṉṉūl 252 (அத்தின் அகரம் அகர முனை இல்லை): the அ of an increment after an அ is dropped
        if (!clitic && inc && a == `A && b == `A)
            assert (dr && !dl && !iv);
        // Naṉṉūl 237 (verbs): after ன் ல் a following த் becomes ற், after ண் ள் it becomes ட்
        if (!clitic && verb && b == `THA && (a == `NA || a == `LA))   assert (rv && rb == `RRA);
        if (!clitic && verb && b == `THA && (a == `NNA || a == `LLA)) assert (rv && rb == `TTA);
        // Naṉṉūl 224 (verbs): after ய் ர் ழ் a following க் ச் த் ப் is doubled, when gem is set
        if (!clitic && verb && gem && !pada && (a == `YA || a == `RA || a == `ZHA) && (b == `KA || b == `CA || b == `THA || b == `PA))
            assert (iv && ib == b && !dl && !dr);
        // the glide between two vowels (Naṉṉūl 162): ய் after i e ai, otherwise வ்
        if (!clitic && a_v && b_v && !(inc && a == `A && b == `A) && !(pada && !b_pada) && !(kural && a == `U && a2m))
            assert (iv && !dl && !dr && ib == (front ? `YA : `VA));
        // a clitic acts only by doubling its initial வல்லினம் after a vowel (the doubled sound is b itself)
        if (clitic) assert (!dl && !dr);
        if (clitic && iv) assert (ib == b);

        // 3. hygiene
        if (rv) assert (verb && !clitic && !dr);   // a first sound is replaced only in a verb seam, and not when it is dropped
        if (!verb) assert (!rv);                    // with the verb flag off, nothing is replaced: the noun unit is what it was
        if (dr) assert (inc && !clitic);          // the right form loses its first sound only in coalescence
        if (!iv) assert (ib == 8'h00);            // nothing is inserted unless a rule inserts
        if (dr) assert (!dl && !iv);              // coalescence does nothing else
    end
endmodule
