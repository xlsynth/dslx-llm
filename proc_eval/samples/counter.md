# Counter Proc

## Prompt

Implement a basic counter proc.

This sample uses the explicit proc model: `config` / `init` / `next`.

The proc should:

- be named `Counter`
- have one proc-scoped output channel `out_ch: chan<u32> out`
- start at `u32:0`
- on each activation, send the current count on `out_ch`
- then increment the state by one for the next activation

Only implement the `Counter` proc. The acceptance test proc will be added automatically.

## Prologue

```dslx
// dslx_run_flags: --max_ticks=16
```

## Signature

```dslx-snippet
proc Counter {
    out_ch: chan<u32> out;

    config(out_ch: chan<u32> out) { ... }
    init { u32:0 }
    next(state: u32) { ... }
}
```

## Tests

```dslx-snippet
#[test_proc]
proc CounterTest {
    terminator: chan<bool> out;
    observed: chan<u32> in;

    config(terminator: chan<bool> out) {
        let (counter_p, observed) = chan<u32>("counter");
        spawn Counter(counter_p);
        (terminator, observed)
    }

    init { join() }

    next(tok: token) {
        let (tok, v0) = recv(tok, observed);
        assert_eq(v0, u32:0);
        let (tok, v1) = recv(tok, observed);
        assert_eq(v1, u32:1);
        let (tok, v2) = recv(tok, observed);
        assert_eq(v2, u32:2);
        let (tok, v3) = recv(tok, observed);
        assert_eq(v3, u32:3);
        send(tok, terminator, true)
    }
}
```
