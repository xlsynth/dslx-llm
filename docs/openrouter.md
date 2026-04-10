# Using `dslx-llm` with OpenRouter

This repository can talk to OpenRouter through the existing OpenAI-compatible
provider path. That makes it easy to try arbitrary hosted models without adding
new provider-specific code.

## Prerequisites

You need:

- an OpenRouter API key
- an `xlsynth` tools installation, exposed through `XLSYNTH_TOOLS`
- the Python dependencies for this repository installed

The eval runner uses the OpenAI-compatible client in `provider_openai.py`, so
OpenRouter works by setting the base URL and API key through environment
variables.

## Required environment variables

Set these before running `eval.py` or `proc_eval.py`:

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export PROVIDER="openai"
export XLSYNTH_TOOLS="$HOME/opt/xlsynth/latest"
```

Notes:

- `PROVIDER=openai` is correct here. In this repo, "openai" means "use the
  OpenAI-compatible chat-completions path", which also covers OpenRouter.
- `XLSYNTH_TOOLS` should point at an `xlsynth` release directory that contains
  the DSLX interpreter and stdlib.

## Choosing a model

For built-in local choices, `eval.py` supports `--model`.

For OpenRouter, use `--custom-model-slug` so you can pass any OpenRouter model
ID directly.

Example model slugs:

- `openai/gpt-5.4`
- `openai/gpt-oss-120b`
- `google/gemini-2.5-pro`
- `anthropic/claude-opus-4.6`
- `qwen/qwen3.5-122b-a10b`

## Running a single sample

A simple smoke test:

```bash
python eval.py \
  --custom-model-slug openai/gpt-5.4 \
  --sample majority \
  --max-retries 1
```

Another example with a hosted open-weight model:

```bash
python eval.py \
  --custom-model-slug qwen/qwen3.5-122b-a10b \
  --sample majority \
  --max-retries 1
```

To list available samples:

```bash
python eval.py --list
```

## Running the full scorecard

To evaluate the whole sample suite:

```bash
python eval.py \
  --custom-model-slug google/gemini-2.5-pro \
  --max-retries 1
```

The scorecard prints:

- pass/fail per sample
- first-attempt pass rate
- all-attempt pass rate
- token usage totals collected from the OpenAI-compatible response schema

## Proc samples

The same environment setup works for proc-oriented evaluation:

```bash
python proc_eval.py \
  --custom-model-slug openai/gpt-5.4 \
  --sample counter \
  --max-retries 1
```

To list proc samples:

```bash
python proc_eval.py --list
```

## Provider pinning for OpenRouter

This repo supports OpenRouter provider routing hints through environment
variables.

If a model is flaky or slow on the default route, you can pin a provider:

```bash
export OPENROUTER_PROVIDER_ONLY="alibaba"
export OPENROUTER_ALLOW_FALLBACKS="false"
```

That is forwarded as an OpenRouter `provider` override in the request body.

You can also specify multiple providers:

```bash
export OPENROUTER_PROVIDER_ONLY="parasail,together"
```

Unset these variables to go back to OpenRouter's default routing behavior.

## Timeouts and retries

Useful knobs:

- `--max-retries`: how many repair attempts the evaluator allows after a
  failing generation
- `--timeout`: request timeout in minutes for one model call
- `--no-critic`: disables the structural requirements critic step

Example:

```bash
python eval.py \
  --custom-model-slug anthropic/claude-opus-4.6 \
  --sample adder_with_carries \
  --max-retries 1 \
  --timeout 5
```

## Notes on benchmark behavior

A model can fail for several distinct reasons:

- invalid DSLX syntax or typing errors
- correct DSLX that fails the sample tests
- structurally valid code that fails the optional critic requirements
- poor instruction-following, such as re-emitting prompt prologue definitions

Using OpenRouter does not change the benchmark semantics. The evaluator still
judges the model by the generated DSLX and the acceptance tests in this repo.

## Troubleshooting

If requests fail immediately:

- verify `OPENAI_API_KEY` and `OPENAI_BASE_URL`
- verify `PROVIDER=openai`
- check that the model slug exists on OpenRouter

If requests hang or are unreliable:

- add `--timeout 5` or another explicit timeout
- try provider pinning with `OPENROUTER_PROVIDER_ONLY`
- reduce concurrency if you are running many single-sample evals in parallel

If DSLX execution fails:

- verify `XLSYNTH_TOOLS`
- confirm the interpreter exists under that directory
- ensure the stdlib path under that installation is intact
