// tamil_noun_gen.sv -- the noun generator with a class INDEX in: the class table (one row per declension class)
// supplies the class values to tamil_noun_gen_core. This is the interface the reference gate drives
// (hdl/tb/tb_noun_gen.v); the class index is latched at `start`.
//
//   cls        the index in phon_rules.STEMFORM (C1..C16, NDBLT, NDBLR, NCLUST, NMURRI)
module tamil_noun_gen (
    input  wire        clk,
    input  wire        rst,
    input  wire        stem_we,
    input  wire [5:0]  stem_wa,
    input  wire [7:0]  stem_wd,
    input  wire        start,
    input  wire [5:0]  stem_len,
    input  wire [4:0]  cls,
    input  wire [3:0]  case_sel,
    input  wire [10:0] flags,
    output wire        busy,
    output wire        out_valid,
    output wire [7:0]  out_byte,
    output wire        out_last,
    output wire        surf_end,
    output wire        all_done
);
`include "gen/tamil_noun_rom.vh"          // the class table, here, in this module's scope
    reg [4:0] r_cls;
    always @(posedge clk) if (start) r_cls <= cls;
    tamil_noun_gen_core core (.clk(clk), .rst(rst), .stem_we(stem_we), .stem_wa(stem_wa), .stem_wd(stem_wd),
                              .start(start), .stem_len(stem_len), .cv(class_rom(r_cls)), .case_sel(case_sel),
                              .flags(flags), .busy(busy), .out_valid(out_valid), .out_byte(out_byte),
                              .out_last(out_last), .surf_end(surf_end), .all_done(all_done));
endmodule
