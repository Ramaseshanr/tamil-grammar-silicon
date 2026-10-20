// tb_noun_stream.v -- end-to-end gate: real stems, one phoneme per cycle.
//
// Streams the TLP1 encoding of every classifiable stem in the gold through
// tamil_noun_front and compares the class against tools/derive_nouns.py.
// This exercises the window extraction -- shift register, length saturation,
// vowel counter -- which the window-level testbench cannot reach.
//
//   cd hdl
//   iverilog -g2012 -o tb/tbs.vvp tb/tb_noun_stream.v rtl/tamil_noun_front.sv gen/tamil_noun_class.v
//   vvp tb/tbs.vvp
`timescale 1ns/1ps
module tb;
    reg        clk = 0, rst = 1, valid = 0, last = 0;
    reg  [7:0] ph = 0;
    wire [4:0] cls;
    wire       ok, done;

    tamil_noun_front dut (.clk(clk), .rst(rst), .ph(ph), .valid(valid), .last(last),
                          .cls(cls), .ok(ok), .done(done));

    always #5 clk = ~clk;

    integer    fd, got, i, n, pass, fail;
    reg [31:0] nb, e_cls, e_ok, byteval;
    reg [7:0]  pbuf [0:63];

    task step; begin @(posedge clk); #1; end endtask

    initial begin
        fd = $fopen("vectors/stem_vectors.hex", "r");
        if (fd == 0) $fatal(1, "cannot open vectors/stem_vectors.hex -- run tools/gen_hdl.py, and vvp from hdl/");
        @(posedge clk); #1; rst = 0;
        n = 0; pass = 0; fail = 0;
        while (!$feof(fd)) begin
            got = $fscanf(fd, "%h %h %h", nb, e_cls, e_ok);
            if (got == 3) begin
                for (i = 0; i < nb; i = i + 1) begin
                    got = $fscanf(fd, "%h", byteval);
                    pbuf[i] = byteval[7:0];
                end
                for (i = 0; i < nb; i = i + 1) begin
                    ph    = pbuf[i];
                    valid = 1'b1;
                    last  = (i == nb - 1);
                    step;
                end
                valid = 1'b0; last = 1'b0;
                // `done` is registered on the last phoneme's edge, so it is asserted now
                n = n + 1;
                if (!done) begin
                    fail = fail + 1;
                    if (fail <= 10) $display("  NO DONE after %0d phonemes (stem %0d)", nb, n);
                end else if (cls !== e_cls[4:0] || ok !== e_ok[0]) begin
                    fail = fail + 1;
                    if (fail <= 10)
                        $display("  MISMATCH stem %0d (%0d phonemes): hw cls=%0d ok=%0b   py cls=%0d ok=%0b",
                                 n, nb, cls, ok, e_cls[4:0], e_ok[0]);
                end else begin
                    pass = pass + 1;
                end
                step;   // one idle cycle between stems
            end
        end
        $fclose(fd);
        $display("");
        $display("  stems streamed : %0d", n);
        $display("  agree with py  : %0d", pass);
        $display("  MISMATCHES     : %0d", fail);
        if (n == 0) $fatal(1, "no vectors read");
        if (fail != 0) $fatal(1, "the datapath disagrees with tools/derive_nouns.py");
        $display("");
        $display("  PASS -- every stem in the gold classifies identically in RTL.");
        $finish;
    end
endmodule
