// The one rule Naṉṉūl 164 states (a short உ after a consonant drops before a vowel), alone, as the condition
// tamil_join.sv's branch P5 tests: twelve input bits. syn/ecp5_p5.ys synthesizes it, to count the lookup tables a rule
// of this size needs.
module p5_rule (input wire [7:0] a, input wire a2m, input wire [7:0] b, input wire kural, output wire drop_left);
  assign drop_left = kural & (a == 8'h02) & (b[7:6] == 2'b00) & a2m;
endmodule
