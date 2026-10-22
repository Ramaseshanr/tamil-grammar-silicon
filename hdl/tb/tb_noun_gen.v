// tb_noun_gen.v -- the oracle gate for the noun generator.
//
// Each record of vectors/gen_vectors.hex is one cell: a stem, its class, a case bundle, and the SET of
// surface forms tools/phon_rules.derive() licenses for it. The testbench loads the stem, starts the
// generator, collects every form it streams out (forms can repeat; they are de-duplicated) and requires
// the two sets to be equal.
//
//   cd hdl
//   python3 ../tools/gen_noun_gen_hdl.py --sample 4000
//   iverilog -g2012 -I. -o tb/tbg.vvp tb/tb_noun_gen.v rtl/tamil_noun_gen.sv rtl/tamil_join.sv && vvp tb/tbg.vvp
//   vvp tb/tbg.vvp +vec=PATH     # another vector file, e.g. the full one from --full --out PATH
//   vvp tb/tbg.vvp +vec=PATH +show   # also print every form the hardware produced (tools/hw_demo.py decodes them)
`timescale 1ns/1ps
module tb;
    reg clk = 0, rst = 1;
    always #5 clk = ~clk;

    reg stem_we = 0; reg [5:0] stem_wa = 0; reg [7:0] stem_wd = 0;
    reg start = 0; reg [5:0] stem_len = 0; reg [4:0] cls = 0; reg [3:0] case_sel = 0; reg [7:0] flags = 0;
    wire busy, out_valid, out_last, surf_end, all_done; wire [7:0] out_byte;

    tamil_noun_gen dut (.clk(clk), .rst(rst), .stem_we(stem_we), .stem_wa(stem_wa), .stem_wd(stem_wd),
                        .start(start), .stem_len(stem_len), .cls(cls), .case_sel(case_sel), .flags(flags),
                        .busy(busy), .out_valid(out_valid), .out_byte(out_byte), .out_last(out_last),
                        .surf_end(surf_end), .all_done(all_done));

    integer fd, got, i, j, k, cells, pass, fail, total_hw;
    reg [8*256-1:0] vecfile; reg show;
    reg [31:0] w;
    reg [31:0] slen, scls, scase, sflags, nexp;
    reg [7:0]  stem_b [0:63];
    // expected forms and hardware forms: up to 64 forms of up to 64 bytes (the generator's buffer size)
    reg [7:0] exp_b [0:64*64-1]; integer exp_l [0:63];
    reg [7:0] hw_b  [0:64*64-1]; integer hw_l  [0:63]; integer nhw;
    integer cur_l; reg [7:0] cur_b [0:63];
    integer cap_i, hit, dup, ok_cell, bytes_seen;
    reg [31:0] ebyte;

    task automatic add_hw_form;
        integer a, bb; reg same;
        begin
            dup = 0;
            for (a = 0; a < nhw; a = a + 1) if (hw_l[a] == cur_l) begin
                same = 1; for (bb = 0; bb < cur_l; bb = bb + 1) if (hw_b[a*64+bb] !== cur_b[bb]) same = 0;
                if (same) dup = 1;
            end
            if (!dup) begin
                if (nhw < 64) begin hw_l[nhw] = cur_l; for (bb = 0; bb < cur_l; bb = bb + 1) hw_b[nhw*64+bb] = cur_b[bb]; end
                nhw = nhw + 1;
            end
        end
    endtask

    initial begin
        if (!$value$plusargs("vec=%s", vecfile)) vecfile = "vectors/gen_vectors.hex";
        show = $test$plusargs("show");
        fd = $fopen(vecfile, "r");
        if (fd == 0) $fatal(1, "cannot open vectors/gen_vectors.hex -- run tools/gen_noun_gen_hdl.py, and vvp from hdl/");
        cells = 0; pass = 0; fail = 0; total_hw = 0;
        repeat (4) @(posedge clk); rst = 0; @(posedge clk);
        while (!$feof(fd)) begin
            got = $fscanf(fd, "%h %h %h %h", slen, scls, scase, sflags);
            if (got == 4) begin
                for (i = 0; i < slen; i = i + 1) begin got = $fscanf(fd, "%h", w); stem_b[i] = w[7:0]; end
                got = $fscanf(fd, "%h", nexp);
                for (j = 0; j < nexp; j = j + 1) begin
                    got = $fscanf(fd, "%h", w); exp_l[j] = w;
                    for (k = 0; k < exp_l[j]; k = k + 1) begin got = $fscanf(fd, "%h", w); exp_b[j*64+k] = w[7:0]; end
                end
                // load the stem
                for (i = 0; i < slen; i = i + 1) begin
                    @(posedge clk); stem_we <= 1; stem_wa <= i; stem_wd <= stem_b[i];
                end
                @(posedge clk); stem_we <= 0;
                stem_len <= slen[5:0]; cls <= scls[4:0]; case_sel <= scase[3:0]; flags <= sflags[7:0];
                @(posedge clk); start <= 1; @(posedge clk); start <= 0;
                // collect
                nhw = 0; cur_l = 0;
                while (!all_done) begin
                    @(posedge clk);
                    if (out_valid) begin cur_b[cur_l] = out_byte; cur_l = cur_l + 1; end
                    if (surf_end) begin add_hw_form; cur_l = 0; end
                end
                if (show) for (i = 0; i < nhw; i = i + 1) begin
                    $write("FORM %0d", cells);
                    for (k = 0; k < hw_l[i]; k = k + 1) $write(" %02h", hw_b[i*64+k]);
                    $display("");
                end
                // compare as sets
                ok_cell = (nhw == nexp);
                for (j = 0; j < nexp && ok_cell; j = j + 1) begin
                    hit = 0;
                    for (i = 0; i < nhw; i = i + 1) if (hw_l[i] == exp_l[j]) begin
                        hit = 1; for (k = 0; k < exp_l[j]; k = k + 1) if (hw_b[i*64+k] !== exp_b[j*64+k]) hit = 0;
                        if (hit) i = nhw;
                    end
                    if (!hit) ok_cell = 0;
                end
                cells = cells + 1; total_hw = total_hw + nhw;
                if (ok_cell) pass = pass + 1;
                else begin
                    fail = fail + 1;
                    if (fail <= 8) begin
                        $write("  MISMATCH cell %0d: class %0d case %0d flags %02h stem", cells, scls, scase, sflags[7:0]);
                        for (i = 0; i < slen; i = i + 1) $write(" %02h", stem_b[i]);
                        $display("  expected %0d forms, hardware %0d", nexp, nhw);
                    end
                end
            end
        end
        $fclose(fd);
        $display("");
        $display("  cells driven   : %0d", cells);
        $display("  forms from hw  : %0d", total_hw);
        $display("  sets equal     : %0d", pass);
        $display("  MISMATCHES     : %0d", fail);
        if (fail != 0) $fatal(1, "noun generator disagrees with tools/phon_rules.py");
        $finish;
    end
    initial begin #100000000000; $display("TIMEOUT"); $fatal(1, "timeout"); end   // 100 s of simulated time; the full set needs about 6
endmodule
