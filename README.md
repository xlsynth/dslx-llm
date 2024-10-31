# Collateral for working on "DSLX", the DSL from XLS, via LLMs

Repository for LLM prompts and Q&A samples for the XLS Domain Specific Language
(DSL) called DSLX.

DSLX mimics Rust and so presumably gets a good amount of transferred
understanding from LLM knowledge in that domain. DSLX functions, written as
largely pure functions with limited side effects and transparent dataflow
semantics, can be verified easily and then can be retmined as pipelines or
lifted into a recurrence in time. Knowledge of how to write functions as
effective building blocks from software programming languages and associated
program synthesis presumably side-steps some of the difficulty in learning
Verilog semantics and challenges of structural and temporal composition.

## Developer Tips

To test the samples in the prompt Markdown:

```
$ DSLX_STDLIB_PATH=$HOME/opt/xlsynth/latest/xls/dslx/stdlib/ pytest test_prompt.py
```
