I’m going to teach you to write DSLX code through examples. DSLX is the Domain Specific Language for XLS. It’s similar to Rust but differs in key ways so you must pay attention to the differences.

To count the number of bits in a `u32`:

```dslx
import std;  // import standard library
fn count_bits(x: u32) -> u32 { std::popcount(x) }  // call library function
```

Note that there is no `mod` keyword to define a scoped module like there is in Rust — in DSLX all modules are single files. This is how we write a test for the function we made

```dslx
#[test]
fn test_count_bits() {
    assert_eq(count_bits(u32:0), u32:0);  // 0 value has 0 bits set
    assert_eq(count_bits(u32:1), u32:1);  // 1 value has 1 bit set
    assert_eq(count_bits(u32:2), u32:1);  // 2 value has 1 bit set
}
```

Note the differences from Rust well: all literals must be prefixed with their type and a colon. Instead of `assert_eq!` being a macro as it is in Rust it is a built-in function so it has no exclamation mark.

**Standard Library Function for Bit-widths** `std::clog2(x)` is the standard library function that computes `ceil(log2(x))` which is often useful for determining bit-widths required to hold a binary number of a particular count of items. It gives back the same width type (unsigned integer) that it takes in.

**Compile-Time Assertions** In DSLX the `const_assert!(cond)` built-in is available for compile-time checks of preconditions. This can be useful for asserting properties of parametric integer values or properties of compile-time constants.

**Enums Require Underlying Width** Unlike in Rust in DSLX we have to note what the integer type underlying an enum is, and enums cannot be sum types as in Rust; in DSLX:

```dslx
enum MyEnum: u8 { A = 0, B = 7, C = 255 }
```

**Array Type Syntax** Array types are written with different syntax from Rust; in Rust we’d write `[u8; 4]` but in DSLX we write `u8[4]`. For multi-dimensional arrays in Rust we’d write `[[u8; 4]; 2]` but in DSLX we write `u8[4][2]` . Indexing works similarly to Rust, we index the outer array before indexing the inner array; i.e. we index the `2` dimension and we get a `u8[4]` and we subsequently index that.

```dslx
#[test]
fn show_2d_indexing() {
    const A: u8[2][3] = [[0, 1], [2, 3], [4, 5]];  // 3 elements that are u8[2]
    assert_eq(A[1][0], u8:2);  // the first index `1` gives us the middle u8[2]
}
```

**Immutable Array Updates** All values are immutable in DSLX, there is no `let mut` as there is in Rust. As a result, immutable arrays are updated via the `update` builtin:

```dslx
#[test]
fn show_array_update() {
    let a: u8[3] = [1, 2, 3];
    let b: u8[3] = update(a, 1, u8:7); // update index `1` to be value `u8:7`
    assert_eq(b, u8[3]:[1, 7, 3])
}
```

**Repeated Array Elements Shorthand** Since it is commonly needed, in DSLX there is a shorthand for repeating an element to fill the remainder of an array:

```dslx
#[test]
fn show_array_fill_notation() {
    let a: u8[7] = [0, ...];
    assert_eq(a, u8[7]:[0, 0, 0, 0, 0, 0, 0]);
}
```

**All-Zero Value Built-In** Since it is commonly needed, in DSLX you can create an “all zero” valued datatype easily with the `zero!` built-in, even if it has aggregates and enums:

```dslx
enum MyEnum: u1 { ONLY_VALUE = 0 }
struct MyStruct { my_field: u2, my_enum_field: MyEnum }
#[test]
fn show_zero_builtin() {
    let s = zero!<MyStruct>();
    assert_eq!(s, MyStruct { my_field: u2:0, my_enum_field: MyEnum::ONLY_VALUE })
}
```

**For Loops** For loops are particularly different from Rust — they are more like “inline tail calls” in DSLX, where an initial accumulator value is passed in, that value is evolved across the course of iterations, and the result value comes out of the for-loop evaluation:

```dslx
#[test]
fn show_for_loop_evolves_accumulator() {
    let a = u32[4]:[0, 1, 2, 3];
    let result: u32 = for (element, accum) in a {  // accumulator often abbreviated `accum`
			let new_accum = accum + element;
			new_accum  // The result of the for-loop body is the new accumulator.
		}(u32:0);  // The initial value of the accumulator is given as zero here.
    assert_eq(result, u32:6)
}
```

**No While Loops** Since functions in DSLX are not turing-complete there are no while loops, everything must be done with bounded loops; i.e. counted `for` loops. This is different from Rust.

**Range Builtin for Iota** To make an array that’s filled with a range of values (sometimes also called “iota”) use the `range` builtin:

```dslx
#[test]
fn show_range_as_array_filled_with_sequentials() {
    assert_eq(range(u32:0, u32:4), u32[4]:[0, 1, 2, 3]);
    assert_eq(range(u32:1, u32:3), u32[2]:[1, 2]);
}
```

**Casts** Casts of primitive integer types are similar to Rust, and sign/zero extension follow the same rules, even though more arbitrary bit-widths are permitted. Just recall that literals have the leading type-and-colon annotation, whereas casts use `as` for the casting operator:

```dslx
#[test]
fn show_cast_of_a_literal() {
    let x = s8:-1;
    let y = x as u8;
    assert_eq(y, u8:0xff);

    // Widening uses the source type to determine whether sign extension
    // is performed, as in Rust.
    let z = x as u16;
    assert_eq(z, u16:0xffff)
}
```

**Parameterized Functions** Parameterized functions in DSLX are similar to, but more powerful than, const generics in Rust. Parameterization in DSLX can do fairly arbitrary computation, and the syntax is shaped like so — note that any “derived parametric” values where we compute them based on other parametrics syntactically have their expressions in curls:

```dslx
/// A parametric function that doubles the width of its input.
fn parametric_widen_2x<X: u32, Y: u32 = {X+X}>(x: uN[X]) -> uN[Y] {
    x as uN[Y]
}

#[test]
fn show_parametric_widen_2x() {
    assert_eq(parametric_widen_2x(u2:2), u4:2);
    assert_eq(parametric_widen_2x(u4:7), u8:7);
    assert_eq(parametric_widen_2x(u7:42), u14:42);
}
```

Also observe that the parametric `X` is filled in implicitly by the argument type in the above example, but explicit instantiation is also allowed:

```dslx
#[test]
fn show_parametric_widen_2x_explicit() {
     assert_eq(parametric_widen_2x<u32:2>(u2:2), u4:2);
}
```

That is all of the tutorial content.

---

Q: Now try to write an LFSR implementation in DSLX. Make it parameterized on number of bits, bitmask for taps, and whether we invert the feedback bit.
