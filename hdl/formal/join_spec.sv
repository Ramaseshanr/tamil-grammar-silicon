// join_spec.sv -- the juncture rules as a flat specification: one guard per rule, no nesting.
//
// tamil_join.sv writes the rules as a chain of if / else-if, so a rule is reached only when every earlier branch
// failed. Here each rule is a GUARD (the full condition under which its verse applies), and a rule fires when its guard
// holds and no earlier guard does. That is the same priority, said differently: it is the second statement of the
// rules that formal/join_equiv.sv holds tamil_join.sv to, for every input.
//
// Order (the order of tools/phon_rules.py join()):  clitic, P9, pada filter, P5, P6, P3, P1, P2, P11, P4.
`include "gen/tamil_phon.vh"

module join_spec (
    input  wire [7:0] a,
    input  wire       a2m,
    input  wire [7:0] b,
    input  wire [7:0] flags,        // {pada, gem, clitic, kural, inc, dbl, mono, nohard}
    output wire       drop_left,
    output wire       ins_v,
    output wire [7:0] ins_b,
    output wire       drop_right
);
    wire pada = flags[7], gem = flags[6], clitic = flags[5], kural = flags[4];
    wire inc  = flags[3], dbl = flags[2], mono   = flags[1], nohard = flags[0];

    wire a_v = (a[7:6] == 2'b00), b_v = (b[7:6] == 2'b00);
    wire a_mey = (a[7:6] == 2'b01);
    wire b_val = (b[7:4] == 4'h4), a_mel = (a[7:4] == 4'h5);
    wire b_pada = (b == `CA) || (b == `TTA) || (b == `THA) || (b == `PA);
    wire front = a[0] && (a[2:0] != 3'b111);
    wire hard_a = (a == `LA) || (a == `LLA) || (a == `NA);

    // the guards, in priority order
    wire g_clitic = clitic;                                          // a clitic: only P10 can act, nothing after it is reached
    wire g_p9     = inc && a_v && (a == b);                          // Naṉṉūl 252: coalescence
    wire g_pada   = pada && !b_pada;                                 // at a word boundary only ச் ட் த் ப் act
    wire g_p5     = kural && (a == `U) && b_v && a2m;                // Naṉṉūl 164: the short உ drops before a vowel
    wire g_p6     = a_v && b_v;                                      // a glide between two vowels
    wire g_p3     = pada && a_mel;                                   // nasal loss at a pada juncture
    wire g_p1     = (a == `MA) && b_val && !pada;                    // ம் takes the place of the following வல்லினம்
    wire g_p2     = hard_a && b_val && !pada && !nohard;             // Naṉṉūl 227: ல் ள் ன் harden
    wire g_p11    = mono && a_mey && b_v;                            // Naṉṉūl 205: the final ஒற்று doubles
    wire g_p4     = a_v && b_val && gem && !pada;                    // a வல்லினம் doubles after a vowel

    // a rule fires when its guard holds and no earlier guard does
    wire w_clitic = g_clitic;
    wire w_p9     = !g_clitic && g_p9;
    wire w_pada   = !g_clitic && !g_p9 && g_pada;                    // fires and does nothing
    wire w_p5     = !g_clitic && !g_p9 && !g_pada && g_p5;
    wire w_p6     = !g_clitic && !g_p9 && !g_pada && !g_p5 && g_p6;
    wire w_p3     = !g_clitic && !g_p9 && !g_pada && !g_p5 && !g_p6 && g_p3;
    wire w_p1     = !g_clitic && !g_p9 && !g_pada && !g_p5 && !g_p6 && !g_p3 && g_p1;
    wire w_p2     = !g_clitic && !g_p9 && !g_pada && !g_p5 && !g_p6 && !g_p3 && !g_p1 && g_p2;
    wire w_p11    = !g_clitic && !g_p9 && !g_pada && !g_p5 && !g_p6 && !g_p3 && !g_p1 && !g_p2 && g_p11;
    wire w_p4     = !g_clitic && !g_p9 && !g_pada && !g_p5 && !g_p6 && !g_p3 && !g_p1 && !g_p2 && !g_p11 && g_p4;

    // P10: a particle doubles its initial வல்லினம் after a vowel (the only thing a clitic does)
    wire w_p10 = w_clitic && dbl && b_val && a_v;

    assign drop_right = w_p9;
    assign drop_left  = w_p5 | w_p3 | w_p1 | w_p2;
    assign ins_v      = w_p10 | w_p6 | w_p1 | w_p2 | w_p11 | w_p4;
    assign ins_b      = ({8{w_p10}} & b)
                      | ({8{w_p6}}  & (front ? `YA : `VA))
                      | ({8{w_p1}}  & ((a & 8'hF8) | (b & 8'h07)))
                      | ({8{w_p2}}  & ((a & 8'h07) | 8'h40))
                      | ({8{w_p11}} & a)
                      | ({8{w_p4}}  & b);
endmodule
