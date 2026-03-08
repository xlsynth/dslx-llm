I’m going to teach you to write DSLX procs through examples.

For proc tasks, use the explicit `config` / `init` / `next` model:

- `config(...)` wires channels and returns proc members as a tuple in declaration order.
- `init { ... }` returns the initial state value.
- `next(state)` or `next(tok: token)` computes the next state and performs any channel communication for one activation.

Important proc rules:

- Use new-style procs with proc-scoped channels.
- Proc members such as channels must be declared in the proc body and returned from `config`.
- Use `send(tok, ch, value)` and `recv(tok, ch)` for channel communication.
- A proc test should use `#[test_proc]`.
- A `#[test_proc]` proc’s `config` function should only take `terminator: chan<bool> out`.
- End a successful test proc activation by sending `true` on the terminator channel: `send(tok, terminator, true)`.
- If a test proc needs to sequence multiple `recv` / `send` operations in one activation, using `token` state is a straightforward pattern.

Example:

```dslx
proc Toggle {
    out_ch: chan<bool> out;

    config(out_ch: chan<bool> out) {
        (out_ch,)
    }

    init { false }

    next(state: bool) {
        let tok = join();
        let tok = send(tok, out_ch, state);
        !state
    }
}

#[test_proc]
proc ToggleTest {
    terminator: chan<bool> out;
    observed: chan<bool> in;

    config(terminator: chan<bool> out) {
        let (toggle_p, observed) = chan<bool>("toggle");
        spawn Toggle(toggle_p);
        (terminator, observed)
    }

    init { join() }

    next(tok: token) {
        let (tok, v0) = recv(tok, observed);
        assert_eq(v0, false);
        let (tok, v1) = recv(tok, observed);
        assert_eq(v1, true);
        let (tok, v2) = recv(tok, observed);
        assert_eq(v2, false);
        send(tok, terminator, true)
    }
}
```

When asked for a proc solution, reply with only the DSLX code that implements the requested proc or procs. Do not include explanation text.
