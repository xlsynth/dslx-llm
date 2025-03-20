# Collateral for working on "DSLX", the DSL from XLS, via LLMs

Repository for LLM prompts and Q&A samples for the XLS Domain Specific Language
(DSL) called DSLX.

## Structure of this project

* `prompt.md`: "prelude" for making a query of an LLM for some synthesizable
  hardware computation. Paste this in to your LLM interface first before a
  sample prompt.
* `samples/*.md`: sample prompts and acceptance tests that can cause an LLM
  response to be accepted/rejected for the associated prompt.
* `test_prompt.py`: a `pytest` based test file that extracts all the DSLX code
  blocks from the prompt and runs them against an interpreter binary to
  determine that they all pass. This is useful to help ensure the prompt is
  showing correct and complete examples as we add/expand its content.
* `eval.py`: feeds the system prompt and sample prompt(s) to a model API and
  tests them against the acceptance tests, feeding back any errors that occur
  up to a max retry count. Emits a scorecard at the end as a success indicator.

To run eval on a specific sample:

```sh
export OPENAI_API_KEY=""  # replace with your key
export XLSYNTH_TOOLS=""  # replace with xlsynth tools dir via github.com/xlsynth/xlsynth/releases
python eval.py --model gpt-3.5-turbo --sample saturating_addsub --max-retries 5
```

## Making the case for DSLX over Verilog

Some arguments in favor of LLMs targeting DSLX over the underlying Verilog:

* **XLS as platform:** The DSL (DSLX) is a fairly lightweight layer on top of
  XLS IR. XLS IR provides a **platform** for analysis and transformation that
  is fully open source with fully defined semantics and equal representative
  capabilities.  XLS lives "underneath" and completely understands the hardware
  computation descriptions, and is capable of **simulating them at naive speed**.

  We can write and slot-in new analysis tools easily, and our understanding of
  the platform is complete -- this is a major challenge for all RTL toolchains
  and Verilog/SystemVerilog semantics in general, often the ones used in practice
  are proprietary and the SystemVerilog support for fully open toolchains is
  partial at best.
* **Transfer learning from Rust and software:** DSLX mimics Rust and so
  presumably gets a good amount of transferred
  understanding from LLM knowledge of function/program construction in the
  software domain.
* **Function-oriented for easy retargeting/composition:** DSLX functions are written as:
  * largely pure functions, with limited side effects and immutable values
  * with transparent dataflow semantics
  * and no undefined behavior,

  and so can be **verified easily** and then can be **retmined as pipelines**
  (via XLS' scheduler) or lifted into a recurrence in time (via `proc`s, for
  stateful evolution (i.e. **generate a state machine**), similar to how we
  reason about loops in turing complete languages).
* **Not deep-inductive, tricky-state-space oriented:** Knowledge of how to
  write functions as effective building blocks from
  software programming languages and associated program synthesis presumably
  side-steps some of the difficulty in learning Verilog semantics and challenges
  of structural and temporal composition.
  * Verilog semantically offers a flat program that is *inherently* operating
    in time, operationally mutating deep state spaces, with undefined behavior.
    Type promotion and matching in expressions is even difficult for expert
    humans to understand and use correctly, in addition to a slew of
    "best practices" required to avoid [traps around 4-value
    semantics](http://www.sunburst-design.com/papers/CummingsSNUG1999Boston_FullParallelCase_rev1_1.pdf).
  * Verilog tools often have implementation-defined but
    **cross-implementation-undefined / specification-undefined** behavior --
    i.e. behavior that is not fully defined by the specification, but that will
    coincidentally have some semantics for a given tool. This is abundant as a
    language becomes less fully-specified.

    Overfitting for the observed behavior of a single tool and believing it is
    specified due to empirical observations is a natural trap. "Transfer
    learning" from the observed semantics of one tool to expectations of what
    another tool will do is tempting, but will likely lead to incorrect results
    due to well-defined vs implementation-defined semantics confusion.
* **Straightforwardly composable primitives (i.e. libraries work):**
  the DSL has a standard library of functions that can be composed without fear
  of correctness errors due to the latency-insensitive nature of the design
  descriptions. As more standard library functions are built/offered, and more
  "batteries included" modules are created, LLMs will be able to leverage
  straightforward notions of composition from a more powerful basis.
  Composition is more challenging in a timed and transition-based programming
  model.

In summary, targeting a slightly **higher level** and **more well defined** set
of constructs that are **more semantically similar to software** should aid in
the construction of **correct, robust hardware computation**.

**By analogy to software High Level Languages:** we don't try to get LLMs to
emit correct assembly from natural descriptions because they get an uplift from
the higher level semantics in a similar fashion to how humans get a
productivity, reasoning, and correctness uplift from the higher level languages
we use.

## Developer Tips

To test the samples in the prompt Markdown:

```shell
DSLX_STDLIB_PATH=$HOME/opt/xlsynth/latest/xls/dslx/stdlib/ pytest test_prompt.py
```

## Ideas not yet added

* Various hashers and PRNGs, e.g. `xoshiro256**` and similar.
* More arbiters: LRU, round robin, hierarchical round robin (via composition).

## Ideas that are too simple

* Parity: this is simply a call to the `std::popcount` function <https://google.github.io/xls/dslx_std/#stdpopcount>
* Bit Reversal: this is simply a call to the `rev` built-in function <https://google.github.io/xls/dslx_std/#rev>
* One-Hot Encoder: this is simply a call to the `encode` built-in function <https://google.github.io/xls/dslx_std/#encode>
