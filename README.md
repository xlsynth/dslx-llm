# Collateral for working on "DSLX", the DSL from XLS, via LLMs

Repository for LLM prompts and Q&A samples for the XLS Domain Specific Language
(DSL) called DSLX.

## Structure of this project

* `prompt.md`: "prelude" for making a query of an LLM for some synthesizable
  hardware computation. Paste this in to your LLM interface first before a
  sample prompt.
* `samples/*.md`: sample prompts and acceptance tests that can cause an LLM
  response to be accepted/rejected for the associated prompt.

## Making the case for DSLX over Verilog

Some arguments in favor of LLMs targeting DSLX over the underlying Verilog:

* DSLX mimics Rust and so presumably gets a good amount of transferred
  understanding from LLM knowledge of function/program construction in the
  software domain.
* DSLX functions are written as:
  * largely pure functions, with limited side effects and immutable values
  * with transparent dataflow semantics
  * and no undefined behavior,
  
  and so can be verified easily and then can be retmined as pipelines (via XLS' scheduler)
  or lifted into a recurrence in time (via `proc`s, for stateful evolution,
  similar to reasoning about loops in turing complete languages).
* Knowledge of how to write functions as effective building blocks from
  software programming languages and associated program synthesis presumably
  side-steps some of the difficulty in learning Verilog semantics and challenges
  of structural and temporal composition.
  * Verilog semantically offers a flat program that is *inherently* operating
    in time, operationally mutating deep state spaces, with undefined behavior.
    Type promotion and matching in expressions is even difficult for expert
    humans to understand and use correctly, in addition to a slew of
    "best practices" required to avoid [traps around 4-value
    semantics](http://www.sunburst-design.com/papers/CummingsSNUG1999Boston_FullParallelCase_rev1_1.pdf). 

## Developer Tips

To test the samples in the prompt Markdown:

```
$ DSLX_STDLIB_PATH=$HOME/opt/xlsynth/latest/xls/dslx/stdlib/ pytest test_prompt.py
```

## Ideas not yet added

* Various hashers and PRNGs, e.g. `xoshiro256**` and similar.
