// tamil_noun_gen.sv -- the Tamil noun generator: a stem, its class and a case bundle in, every
// licensed surface form out, one byte per cycle.
//
// This is tools/noun_gen_model.py as a machine, and that file is phon_rules.derive() restated in
// the shape this needs. It is a transliteration, not a second derivation: the Python is the
// authority, and hdl/tb/tb_noun_gen.v drives this module with stems, classes and bundles from the
// reference and compares the whole SET of forms with phon_rules.derive().
//
// What it does, in order, for each choice of options (an odometer walks them all):
//   1. copy the stem into a working buffer
//   2. STEM-FORM   drop the class's truncation, join the class's linking increment (the சாரியை;
//                  Naṉṉūl 244, 164), or turn a final ன் to ர் before கள் (P8) -- the 80 class values
//   3. MORPHEMES   up to seven slots (plural, சாரியை இன், case உருபு, benefactive, comparative,
//                  focus, sandhi); at each slot it counts the options the state allows (Naṉṉūl 243:
//                  the சாரியை may come, drop or vary) and takes the next one in turn
//   4. each ending is joined at the seam by tamil_join (the sūtra rules: 227 hardening, 164 உ-drop,
//                  assimilation, glides, doubling); the dative after இ ஈ ஐ is கு (P12, Arden 110)
//   5. stream the result; then step the odometer, until every combination has been emitted.
//
// Interface:  load the stem with stem_we/stem_wa/stem_wd (bytes 0..len-1), then pulse `start` with
// stem_len, cls, case_sel and the flags. Each form comes out as out_valid bytes ending with
// out_last; surf_end pulses once per form; all_done pulses after the last form.
//
//   cls        the index in phon_rules.STEMFORM (C1..C16, NDBLT, NDBLR, NCLUST, NMURRI)
//   case_sel   0 none or nominative; 2 acc, 3 inst, 4 dat, 5 loc, 6 abl, 7 gen, 8 soc, 9 so
//   flags      {sandhi[2:0], obl, foc, cmpr, ben, pl}   sandhi: 0 none, 1 க், 2 ச், 3 ப், 4 த்
//
// Forms can repeat (two choices can give one string); the consumer treats the output as a set.
`include "gen/tamil_phon.vh"
`include "gen/tamil_noun_rom.vh"

module tamil_noun_gen (
    input  wire       clk,
    input  wire       rst,
    input  wire       stem_we,
    input  wire [5:0] stem_wa,
    input  wire [7:0] stem_wd,
    input  wire       start,
    input  wire [5:0] stem_len,
    input  wire [4:0] cls,
    input  wire [3:0] case_sel,
    input  wire [7:0] flags,
    output reg        busy,
    output reg        out_valid,
    output reg  [7:0] out_byte,
    output reg        out_last,
    output reg        surf_end,
    output reg        all_done
);
    localparam [4:0] K_PL = 0, K_IN = 1, K_DAT = 4, K_BEN = 10, K_CMPR = 11, K_FOC = 12;

    // ---------------------------------------------------------------- job registers
    reg [5:0] r_len;  reg [4:0] r_cls;  reg [3:0] r_case;
    reg [7:0] rf;
    wire r_pl = rf[0], r_ben = rf[1], r_cmpr = rf[2], r_foc = rf[3], r_obl = rf[4];
    wire [2:0] r_sandhi = rf[7:5];

    // class ROM fields
    wire [40:0] crom = class_rom(r_cls);
    wire        c_plain = crom[40], c_uyar = crom[39], c_dblfin = crom[38], c_gem = crom[37];
    wire [2:0]  c_inclen = crom[36:34];
    wire        c_trunc = crom[33];
    wire [31:0] c_inc = crom[31:0];

    // ---------------------------------------------------------------- memories
    reg [7:0] stem [0:63];
    reg [7:0] buff [0:63];
    always @(posedge clk) if (stem_we) stem[stem_wa] <= stem_wd;

    // ---------------------------------------------------------------- run state
    reg [6:0] blen;
    reg [6:0] ci;
    reg       kur, first, d0;
    reg [1:0] base_c, nbase;
    reg [3:0] c [0:6];
    reg [3:0] n [0:6];
    reg [2:0] si;
    reg [3:0] cand, cnt;
    reg       found;
    reg [7:0] mb [0:7];
    reg [3:0] mlen;
    reg [3:0] mj;
    reg [7:0] mflags;
    reg       mis_in;                 // the slot being executed is the சாரியை இன்
    reg [1:0] ret;                    // what to do when an append finishes
    localparam R_INC = 2'd0, R_SLOT = 2'd1;

    // ---------------------------------------------------------------- the seam
    wire [6:0] bl1 = (blen == 0) ? 7'd0 : blen - 7'd1;
    wire [7:0] last_b  = (blen == 0) ? 8'h00 : buff[bl1];
    wire [7:0] last_b2 = (blen < 2)  ? 8'h00 : buff[blen - 7'd2];
    wire       a2m = (blen >= 2) && (last_b2[7:6] == 2'b01);
    wire       j_dl, j_iv, j_dr; wire [7:0] j_ib;
    tamil_join seam (.a(last_b), .a2m(a2m), .b(mb[0]), .flags(mflags),
                     .drop_left(j_dl), .ins_v(j_iv), .ins_b(j_ib), .drop_right(j_dr));

    // ---------------------------------------------------------------- slots
    reg        s_act;  reg [4:0] s_kind;
    always @* begin
        case (si)
            3'd0: begin s_act = r_pl;                          s_kind = K_PL;  end
            3'd1: begin s_act = (r_case == 4'd2) || (r_case == 4'd3) || (r_case == 4'd6) || (r_case == 4'd7);
                                                               s_kind = K_IN;  end
            3'd2: begin s_act = (r_case != 4'd0);              s_kind = {1'b0, r_case}; end
            3'd3: begin s_act = r_ben;                         s_kind = K_BEN; end
            3'd4: begin s_act = r_cmpr;                        s_kind = K_CMPR; end
            3'd5: begin s_act = r_foc;                         s_kind = K_FOC; end
            default: begin s_act = (r_sandhi != 3'd0);         s_kind = 5'd12 + {2'b00, r_sandhi}; end
        endcase
    end
    wire s_is_case = (s_kind >= 5'd2) && (s_kind <= 5'd9);
    wire s_clitic  = (s_kind == K_CMPR) || (s_kind == K_FOC);

    // ---------------------------------------------------------------- one candidate of the scan
    wire [1:0]  cai = cand[3:2], cvi = cand[1:0];
    wire [69:0] mrom = morph_rom(s_kind, cai);
    wire        m_ex = mrom[69], m_starts_in = mrom[68];
    wire [3:0]  m_len = mrom[67:64];
    wire [63:0] m_bytes = mrom[63:0];
    wire        m_empty = (m_len == 4'd0);
    wire        p12 = (s_kind == K_DAT) && (cai == 2'd0) && last_b[7:6] == 2'b00
                      && (last_b[2:0] == 3'd1 || last_b[2:0] == 3'd5) && (blen != 0);
    wire        front_iu = (last_b[7:6] == 2'b00) && (last_b[2:0] == 3'd1 || last_b[2:0] == 3'd5) && (blen != 0);
    wire        no_irku = (s_kind == K_DAT) && (cai != 2'd0) && front_iu;   // after இ ஈ ஐ: கு only, no இற்கு
    wire        g_eff = c_gem | p12;
    wire [3:0]  u_len = p12 ? 4'd2 : m_len;
    wire [63:0] u_bytes = p12 ? 64'h0000_0000_0000_0240 : m_bytes;       // க் (0x40), உ (0x02)
    wire        pada_here = (si == 3'd6);
    wire        var_ok = (cvi == 2'd0) ? 1'b1 :
                         (cvi == 2'd1) ? (c_dblfin & first) :
                         (cvi == 2'd2) ? s_clitic : first;
    wire        cand_ok = (cand < 4'd12) && m_ex && !no_irku && !(s_is_case && d0 && m_starts_in)
                          && (m_empty ? (cvi == 2'd0) : var_ok);
    reg  [7:0]  cflags;
    always @* begin
        case (cvi)
            2'd0: cflags = {pada_here, g_eff, s_clitic, kur, 4'b0000};
            2'd1: cflags = {pada_here, g_eff, s_clitic, kur, 4'b0010};
            2'd2: cflags = 8'b0010_0100;                                     // clitic + doubling, nothing else
            default: cflags = {pada_here, g_eff, s_clitic, kur, 4'b0001};
        endcase
    end

    // ---------------------------------------------------------------- stem-form decision
    wire [6:0] new_len = c_trunc ? {1'b0, r_len} - 7'd1 : {1'b0, r_len};
    wire [7:0] nl1 = (new_len == 0) ? 8'h00 : buff[new_len - 7'd1];
    wire [7:0] nl2 = (new_len < 2)  ? 8'h00 : buff[new_len - 7'd2];
    wire       excl = (new_len >= 2) && (nl1[7:6] == 2'b01) && (nl1 == nl2) && (c_inc[7:0] == nl1);
    wire [7:0] fin_b = (blen == 0) ? 8'h00 : buff[bl1];

    // ---------------------------------------------------------------- the odometer
    // the highest-index digit that can still advance
    integer q;
    reg [2:0] hj; reg hf;
    always @* begin
        hf = 1'b0; hj = 3'd0;
        for (q = 6; q >= 0; q = q - 1)
            if (!hf && (c[q] + 4'd1 < n[q])) begin hf = 1'b1; hj = q[2:0]; end
    end

    // ---------------------------------------------------------------- the sequencer
    localparam S_IDLE = 4'd0, S_COPY = 4'd1, S_SF0 = 4'd2, S_SF1 = 4'd3, S_SEAM = 4'd4, S_ACOPY = 4'd5,
               S_SLOT = 4'd6, S_SCAN = 4'd7, S_EXEC = 4'd8, S_OUT = 4'd9, S_ADV = 4'd10;
    reg [3:0] st;
    integer t;

    always @(posedge clk) begin
        out_valid <= 1'b0; out_last <= 1'b0; surf_end <= 1'b0; all_done <= 1'b0;
        if (rst) begin
            st <= S_IDLE; busy <= 1'b0;
        end else case (st)
        S_IDLE: if (start) begin
            r_len <= stem_len; r_cls <= cls; r_case <= case_sel; rf <= flags;
            base_c <= 2'd0; for (t = 0; t < 7; t = t + 1) begin c[t] <= 4'd0; n[t] <= 4'd1; end
            ci <= 7'd0; blen <= 7'd0; busy <= 1'b1; st <= S_COPY;
        end
        S_COPY: if (ci < {1'b0, r_len}) begin buff[ci[5:0]] <= stem[ci[5:0]]; ci <= ci + 7'd1; end
                else begin blen <= {1'b0, r_len}; st <= S_SF0; end
        S_SF0: begin
            kur <= 1'b0; first <= 1'b1; d0 <= 1'b0; si <= 3'd0;
            nbase <= 2'd1;
            if (r_obl) begin
                blen <= new_len;
                if (c_inclen != 3'd0 && !excl) begin
                    nbase <= c_plain ? 2'd2 : 2'd1;
                    if (base_c == 2'd1) begin blen <= {1'b0, r_len}; st <= S_SLOT; end   // the plain stem
                    else st <= S_SF1;
                end else st <= S_SLOT;
            end else begin
                if (r_pl && c_uyar && blen != 0 && fin_b == `NA) buff[bl1] <= `RA;    // P8: ன் -> ர் before கள்
                st <= S_SLOT;
            end
        end
        S_SF1: begin                                                    // join the class's linking increment
            for (t = 0; t < 4; t = t + 1) mb[t] <= c_inc[8*t +: 8];
            mlen <= {1'b0, c_inclen}; mflags <= 8'b0000_1000;       // the inc flag only (P9 coalescence)
            ret <= R_INC; st <= S_SEAM;
        end
        S_SEAM: begin
            // apply the seam: drop, insert, then copy the ending from byte dr
            if (j_iv) buff[blen - {6'd0, j_dl}] <= j_ib;
            blen <= blen - {6'd0, j_dl} + {6'd0, j_iv};
            mj <= {3'd0, j_dr}; st <= S_ACOPY;
        end
        S_ACOPY: if (mj < mlen) begin buff[blen] <= mb[mj[2:0]]; blen <= blen + 7'd1; mj <= mj + 4'd1; end
                 else begin
                     kur <= (mb[(mlen - 4'd1) & 4'd7] == `U);
                     if (ret == R_SLOT) begin first <= 1'b0; if (mis_in) d0 <= 1'b1; si <= si + 3'd1; end
                     st <= S_SLOT;
                 end
        S_SLOT: if (si == 3'd7) begin ci <= 7'd0; st <= S_OUT; end
                else if (!s_act) si <= si + 3'd1;
                else begin cand <= 4'd0; cnt <= 4'd0; found <= 1'b0; st <= S_SCAN; end
        S_SCAN: begin
            if (cand < 4'd12) begin
                if (cand_ok) begin
                    if (cnt == c[si] && !found) begin
                        found <= 1'b1; mlen <= u_len; mflags <= cflags; mis_in <= (s_kind == K_IN);
                        for (t = 0; t < 8; t = t + 1) mb[t] <= u_bytes[8*t +: 8];
                    end
                    cnt <= cnt + 4'd1;
                end
                cand <= cand + 4'd1;
            end else begin
                n[si] <= cnt; st <= S_EXEC;
            end
        end
        S_EXEC: begin
            if (mlen == 4'd0) begin si <= si + 3'd1; st <= S_SLOT; end          // the empty alternative
            else begin ret <= R_SLOT; st <= S_SEAM; end
        end
        S_OUT: begin
            if (ci < blen) begin
                out_valid <= 1'b1; out_byte <= buff[ci[5:0]]; out_last <= (ci + 7'd1 == blen);
                ci <= ci + 7'd1;
            end else begin surf_end <= 1'b1; st <= S_ADV; end
        end
        S_ADV: begin
            if (hf) begin
                c[hj] <= c[hj] + 4'd1;
                for (t = 0; t < 7; t = t + 1) if (t > hj) c[t] <= 4'd0;
                ci <= 7'd0; blen <= 7'd0; st <= S_COPY;
            end else if (base_c + 2'd1 < nbase) begin
                base_c <= base_c + 2'd1;
                for (t = 0; t < 7; t = t + 1) c[t] <= 4'd0;
                ci <= 7'd0; blen <= 7'd0; st <= S_COPY;
            end else begin
                all_done <= 1'b1; busy <= 1'b0; st <= S_IDLE;
            end
        end
        default: st <= S_IDLE;
        endcase
    end

endmodule
