//! Tamil noun datapath — the declension classifier, in hardware.
//!
//! Reuses the generator approach of `SanskritOS/hdl_synth`: a RustHDL `LogicBlock`,
//! simulated natively here and emitted as Verilog. Nothing in SanskritOS is touched.
//!
//! WHAT THIS BLOCK IS. `audit/DERIVABILITY.md` established that Tamil noun declension
//! class is a *theorem*, not a table: 40 contexts assign the class of 44,076 stems at
//! 99.77%, a 1,105× compression. That makes it the one part of the grammar that needs no
//! lexicon at all — and therefore the part that belongs in silicon first.
//!
//! WHY IT IS COMBINATIONAL. `tools/derive_nouns.py::context()` reads only the last three
//! phonemes, the stem length, and a count of vowels. Measured over all 43,647 classifiable
//! stems: those five fields give **0 conflicting assignments**, so class is a pure function
//! of 29 bits. The streaming front end that produces them is `Tlp1Window`; this block is
//! the decision, exactly as `shastric_alu` is the decision in SanskritOS.
//!
//! THE AUTHORITY IS THE PYTHON. Following the convention in
//! `SanskritOS/hardware/rtl/anvaya_verify.sv`: this is a faithful transcription of
//! `tools/derive_nouns.py::context()` plus the fitted `classifier` map in
//! `data/derived/noun_rules_paired.json`. Where the two disagree, **the Python is right** —
//! it is what every measurement in `audit/` was made against. `hdl/tb/` checks them against
//! each other over every real stem.
//!
//! TLP1 EARNS ITS KEEP HERE. Every predicate is one mask and one compare, because the
//! encoding was laid out for it: category is bits 7–6, இனம் is bits 5–4, vowel length is
//! bit 3, place is bits 2–0. `is_nedil` is a bit test, not a lookup.

use rust_hdl::prelude::*;

// TLP1 values appear in classify_gen.rs as bare literals, because #[hdl_gen] rejects both
// casts and named constants. For reference, from tools/tlp1.py:
//
//   category  bits 7-6   00 = uyir, 01 = mey        is_mey(b)   = (b & 0xC0) == 0x40
//   இனம்       bits 5-4   val / mel / idai           is_uyir(b)  = (b & 0xC0) == 0x00
//   நெடில்     bit  3     vowel length               is_nedil(b) = is_uyir(b) & (b & 0x08)
//   place     bits 2-0
//
//   உ = 0x02   ட் = 0x42   ற் = 0x45   ன் = 0x55   அ = 0x00
//
// Class codes are assigned by tools/gen_hdl.py and written to gen/tamil_classes.vh.
// 0 means "context not present in the fitted classifier", matching classify() -> None.

/// Combinational declension classifier: 29 bits in, 5-bit class out.
#[derive(LogicBlock)]
pub struct TamilNounClass {
    /// final phoneme (TLP1 byte)
    pub p1: Signal<In, Bits<8>>,
    /// penultimate phoneme, 0 when the stem is 1 phoneme long
    pub p2: Signal<In, Bits<8>>,
    /// antepenultimate phoneme, 0 when the stem is < 3 phonemes
    pub p3: Signal<In, Bits<8>>,
    /// stem length in phonemes, saturating at 4
    pub len: Signal<In, Bits<3>>,
    /// number of uyir in the stem, saturating at 3
    pub uyir: Signal<In, Bits<2>>,

    /// the declension class, valid only when `ok` is high
    /// (named `cls`, not `class`: `class` is a SystemVerilog keyword)
    pub cls: Signal<Out, Bits<5>>,
    /// low when the context is one the fitted classifier has never seen
    pub ok: Signal<Out, Bit>,
}

impl Default for TamilNounClass {
    fn default() -> Self {
        Self {
            p1: Signal::default(),
            p2: Signal::default(),
            p3: Signal::default(),
            len: Signal::default(),
            uyir: Signal::default(),
            cls: Signal::default(),
            ok: Signal::default(),
        }
    }
}

include!("classify_gen.rs");

fn main() {
    let mut hw = TamilNounClass::default();
    hw.connect_all();
    // RustHDL always names the emitted top module `top`; give it its real name so the
    // testbench and the synthesis script can instantiate it.
    let v = generate_verilog(&hw)
        .replace("module top(", "module tamil_noun_class(")
        .replace("endmodule // top", "endmodule // tamil_noun_class");
    let hdr = concat!(
        "// GENERATED from hdl/src/{main,classify_gen}.rs by `cargo run` in hdl/.\n",
        "// Do not edit: regenerate with `python3 tools/gen_hdl.py && cargo run`.\n",
        "// The authority is tools/derive_nouns.py; hdl/tb checks this against it.\n",
    );
    std::fs::write("gen/tamil_noun_class.v", format!("{hdr}{v}")).expect("write verilog");
    println!("wrote gen/tamil_noun_class.v");
}
