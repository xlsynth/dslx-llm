# Traffic Light FSM

## Prompt

Implement one step of a simple traffic-light finite state machine.

The controller has three phases:

- `GREEN`
- `YELLOW`
- `RED`

Use this transition behavior:

- `emergency == true`: immediately go to `RED` and reset the per-phase counter.
- In `GREEN`: stay in `GREEN` and increment `cycles` each step; once `cycles >= 3` and `car_waiting == true`, transition to `YELLOW` and reset `cycles` to zero.
- In `YELLOW`: transition to `RED` after one cycle in yellow.
- In `RED`: transition to `GREEN` after two cycles in red.

Timing semantics are important:

- `cycles` in the input state is the number of already completed steps in the current phase.
- On each call, either increment `cycles` (when staying in the same phase) or reset `cycles` to zero (when transitioning to a different phase).
- Equivalently for thresholds: in `YELLOW`, transition when input `cycles >= 1`; in `RED`, transition when input `cycles >= 2`.

This sample is intentionally a "fill in this state struct" task:
define `TrafficLightState` yourself and return a fully populated value in all paths.
To keep tests decoupled from your internal field names, also implement constructor/accessor helpers.

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
type CycleCount = u4;

enum Phase : u2 {
    GREEN = 0,
    YELLOW = 1,
    RED = 2,
}
```

## Signature

```dslx-snippet
fn make_state(phase: Phase, cycles: CycleCount) -> TrafficLightState
fn get_phase(state: TrafficLightState) -> Phase
fn get_cycles(state: TrafficLightState) -> CycleCount
fn traffic_light_step(car_waiting: bool, emergency: bool, state: TrafficLightState) -> TrafficLightState
```

## Tests

```dslx-snippet
#[test]
fn test_nominal_sequence_with_waiting_car() {
    let state0 = make_state(Phase::GREEN, CycleCount:0);
    let state1 = traffic_light_step(false, false, state0);
    assert_eq(get_phase(state1), Phase::GREEN);
    assert_eq(get_cycles(state1), CycleCount:1);

    let state2 = traffic_light_step(false, false, state1);
    assert_eq(get_phase(state2), Phase::GREEN);
    assert_eq(get_cycles(state2), CycleCount:2);

    let state3 = traffic_light_step(false, false, state2);
    assert_eq(get_phase(state3), Phase::GREEN);
    assert_eq(get_cycles(state3), CycleCount:3);

    // At >=3 green cycles, a waiting car allows transition to yellow.
    let state4 = traffic_light_step(true, false, state3);
    assert_eq(get_phase(state4), Phase::YELLOW);
    assert_eq(get_cycles(state4), CycleCount:0);

    let state5 = traffic_light_step(false, false, state4);
    assert_eq(get_phase(state5), Phase::YELLOW);
    assert_eq(get_cycles(state5), CycleCount:1);

    let state6 = traffic_light_step(false, false, state5);
    assert_eq(get_phase(state6), Phase::RED);
    assert_eq(get_cycles(state6), CycleCount:0);

    let state7 = traffic_light_step(false, false, state6);
    assert_eq(get_phase(state7), Phase::RED);
    assert_eq(get_cycles(state7), CycleCount:1);

    let state8 = traffic_light_step(false, false, state7);
    assert_eq(get_phase(state8), Phase::RED);
    assert_eq(get_cycles(state8), CycleCount:2);

    let state9 = traffic_light_step(false, false, state8);
    assert_eq(get_phase(state9), Phase::GREEN);
    assert_eq(get_cycles(state9), CycleCount:0);
}

#[test]
fn test_green_holds_without_waiting_car() {
    let state_before = make_state(Phase::GREEN, CycleCount:3);
    let state_after = traffic_light_step(false, false, state_before);
    assert_eq(get_phase(state_after), Phase::GREEN);
    assert_eq(get_cycles(state_after), CycleCount:4);
}

#[test]
fn test_emergency_forces_red_from_yellow() {
    let state = make_state(Phase::YELLOW, CycleCount:1);
    let next = traffic_light_step(false, true, state);
    assert_eq(get_phase(next), Phase::RED);
    assert_eq(get_cycles(next), CycleCount:0);
}

#[quickcheck]
fn quickcheck_emergency_always_red(car_waiting: bool, phase_raw: u2, cycles: CycleCount) -> bool {
    let phase = match phase_raw {
        u2:0 => Phase::GREEN,
        u2:1 => Phase::YELLOW,
        _ => Phase::RED,
    };
    let state = make_state(phase, cycles);
    let next = traffic_light_step(car_waiting, true, state);
    get_phase(next) == Phase::RED && get_cycles(next) == CycleCount:0
}
```
