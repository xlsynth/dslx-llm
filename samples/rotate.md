# Rotate With Direction

## Prompt

Implement a rotation routine that can rotate a bits-based value either left or right by a provided amount.

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
enum Direction : u1 {
    LEFT = 0,
    RIGHT = 1,
}
```

## Signature

```dslx-snippet
fn rotate<N: u32, LOG2: u32 = {std::clog2(N)}>(x: uN[N], amount: uN[LOG2], direction: Direction) -> uN[N]
```

## Tests

```dslx-snippet
#[test]
fn test_rotate_left() {
    let x = u4:0b0110;
    assert_eq(rotate(x, u2:0, Direction::LEFT), x);
    assert_eq(rotate(x, u2:1, Direction::LEFT), u4:0b1100);
    assert_eq(rotate(x, u2:2, Direction::LEFT), u4:0b1001);
    assert_eq(rotate(x, u2:3, Direction::LEFT), u4:0b0011);
}

#[test]
fn test_rotate_right() {
    let x = u4:0b0110;
    assert_eq(rotate(x, u2:0, Direction::RIGHT), x);
    assert_eq(rotate(x, u2:1, Direction::RIGHT), u4:0b0011);
    assert_eq(rotate(x, u2:2, Direction::RIGHT), u4:0b1001);
    assert_eq(rotate(x, u2:3, Direction::RIGHT), u4:0b1100);
}

#[quickcheck]
fn quickcheck_rotate_preserves_popcount(x: u4, amount: u2, direction: Direction) -> bool {
    let original_popcount = std::popcount(x);
    let rotated = rotate(x, amount, direction);
    std::popcount(rotated) == original_popcount
}
```
