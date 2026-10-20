// tb_noun_class.v -- the oracle gate for the declension classifier.
//
// Drives every distinct hardware window that occurs in the gold and compares against what
// tools/derive_nouns.py::classify() returned for that window. The Python is the authority;
// one mismatch fails the run.
//
//   cd hdl
//   iverilog -g2005 -o tb/tb.vvp tb/tb_noun_class.v gen/tamil_noun_class.v
//   vvp tb/tb.vvp
`timescale 1ns/1ps
module tb;
    reg  [7:0] p1, p2, p3;
    reg  [2:0] len;
    reg  [1:0] uyir;
    wire [4:0] cls;
    wire       ok;

    tamil_noun_class dut (.p1(p1), .p2(p2), .p3(p3), .len(len), .uyir(uyir),
                          .cls(cls), .ok(ok));

    integer   fd, got, n, pass, fail;
    reg [31:0] v_p1, v_p2, v_p3, v_len, v_uyir, e_cls, e_ok;

    initial begin
        fd = $fopen("vectors/class_vectors.hex", "r");
        if (fd == 0) $fatal(1, "cannot open vectors/class_vectors.hex -- run tools/gen_hdl.py, and vvp from hdl/");
        n = 0; pass = 0; fail = 0;
        while (!$feof(fd)) begin
            got = $fscanf(fd, "%h %h %h %h %h %h %h\n",
                          v_p1, v_p2, v_p3, v_len, v_uyir, e_cls, e_ok);
            if (got == 7) begin
                p1 = v_p1[7:0]; p2 = v_p2[7:0]; p3 = v_p3[7:0];
                len = v_len[2:0]; uyir = v_uyir[1:0];
                #1;
                n = n + 1;
                if (cls !== e_cls[4:0] || ok !== e_ok[0]) begin
                    fail = fail + 1;
                    if (fail <= 10)
                        $display("  MISMATCH p1=%02h p2=%02h p3=%02h len=%0d uyir=%0d : hw cls=%0d ok=%0b   py cls=%0d ok=%0b",
                                 p1, p2, p3, len, uyir, cls, ok, e_cls[4:0], e_ok[0]);
                end else begin
                    pass = pass + 1;
                end
            end
        end
        $fclose(fd);
        $display("");
        $display("  windows driven : %0d", n);
        $display("  agree with py  : %0d", pass);
        $display("  MISMATCHES     : %0d", fail);
        if (n == 0) $fatal(1, "no vectors read");
        if (fail != 0) $fatal(1, "the RTL disagrees with tools/derive_nouns.py");
        $display("");
        $display("  PASS -- the RTL and tools/derive_nouns.py agree on every window.");
        $finish;
    end
endmodule
