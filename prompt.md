I’m going to teach you to write DSLX code through examples. DSLX is the Domain Specific Language for XLS. It’s similar to Rust but differs in key ways so you must pay attention to the differences.

To count the number of bits in a `u32`:

```dslx
import std;  // import standard library
fn count_bits(x: u32) -> u32 { std::popcount(x) }  // call library function

#[test]
fn test_count_bits() {
    assert_eq(count_bits(u32:0), u32:0);  // 0 value has 0 bits set
    assert_eq(count_bits(u32:1), u32:1);  // 1 value has 1 bit set
    assert_eq(count_bits(u32:2), u32:1);  // 2 value has 1 bit set
}
```

Note the differences from Rust: all literals must be prefixed with their type and a colon. Instead of `assert_eq!` being a macro as it is in Rust it is a built-in function so it has no exclamation mark.

**No `mod` keyword** There is no `mod` keyword to define a scoped module like there is in Rust — in DSLX all modules are single files.

**Standard Library Function for Bit-widths** `std::clog2(x)` is the standard library function that computes `ceil(log2(x))` which is often useful for determining bit-widths required to hold a binary number of a particular count of items. It gives back the same width type (unsigned integer) that it takes in.

**Compile-Time Assertions** In DSLX the `const_assert!(cond)` built-in is available for compile-time checks of preconditions. This can be useful for asserting properties of parametric integer values or properties of compile-time constants.

**Width Slices** To slice bits out of a value in DSLX there is a "width slice" syntax that extracts some number of bits (given by a type) from a given starting position in the value -- note that the starting position may be dynamic:

```dslx
#[test]
fn show_width_slice() {
    let x = u16:0xabcd;
    let d: u4 = x[0 +: u4];
    assert_eq(d, u4:0xd);
    let a: u4 = x[12 +: u4];
    assert_eq(a, u4:0xa);
    // Slicing past the end we get zero-fill.
    let past_end = x[14 +: u4];
    assert_eq(past_end, u4:0xa >> 2);
}
```

**Enums Require Underlying Width** Unlike in Rust in DSLX we have to note what the integer type underlying an enum is, and enums cannot be sum types as in Rust; in DSLX:

```dslx
enum MyEnum: u8 { A = 0, B = 7, C = 255 }
```

**Array Type Syntax** Array types are written with different syntax from Rust; in Rust we’d write `[u8; 4]` but in DSLX we write `u8[4]`.

**Multi-Dimensional Array Types and Indexing** For multi-dimensional arrays in Rust we’d write `[[u8; 4]; 2]` but in DSLX we write `u8[4][2]`. Note **very well** that the `2` is the first dimension indexed in that DSLX type! Which is to say, the indexing works similarly to Rust, we index the outer array before indexing the inner array; i.e. we index the `2` dimension and we get a `u8[4]` and we can subsequently index that to get a single `u8`. Don't be fooled by the fact it looks more like C syntax, the first dimension written in the multi-dimensional array type is not the first dimension indexed.

```dslx
#[test]
fn show_2d_indexing() {
    const A = u8[2][3]:[[u8:0, u8:1], [u8:2, u8:3], [u8:4, u8:5]];  // 3 elements that are u8[2]
    assert_eq(A[1][0], u8:2);  // the first index `1` gives us the middle u8[2]
}
```

**Immutable Array Updates** All values are immutable in DSLX, there is no `let mut` as there is in Rust. As a result, immutable arrays are updated via the `update` builtin:

```dslx
#[test]
fn show_array_update() {
    let a = u8[3]:[1, 2, 3];
    let b: u8[3] = update(a, u32:1, u8:7); // update index `1` to be value `u8:7`
    assert_eq(b, u8[3]:[1, 7, 3])
}
```

**Repeated Array Elements Shorthand** Since it is commonly needed, in DSLX there is a shorthand for repeating an element to fill the remainder of an array:

```dslx
#[test]
fn show_array_fill_notation() {
    let a = u8[7]:[0, ...];
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
    assert_eq(s, MyStruct { my_field: u2:0, my_enum_field: MyEnum::ONLY_VALUE })
}
```

**Array Reverse Built-In** DSLX has a built-in primitive for array reversal called `array_rev`:

```dslx
#[test]
fn show_array_rev() {
    let a = u4[3]:[0, 1, 2];
    assert_eq(array_rev(a), u4[3]:[2, 1, 0]);
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
fn parametric_widen_2x<X: u32, Y: u32 = {X+X}>(x: uN[X]) -> uN[Y] { x as uN[Y] }

#[test]
fn show_parametric_widen_2x_explicit() {
     assert_eq(parametric_widen_2x<u32:2>(u2:2), u4:2);
}
```

**Constructing Parameterized Types** It's common to want to construct an type with a number of bits based on a compile-time constant value. `uN` is the unsigned bits type constructor, and `sN` is the signed bits type constructor -- they can be instantiated with a literal value or a constant name or simple expressions. It is often most readable to instantiate them using a named constant:

```dslx
#[test]
fn show_parameterized_type_constructors() {
    const N = u32:4;
    let x = uN[N]:0b1100;
    let y = sN[N]:0b1100;
    assert_eq(y as uN[N], x);
    assert_eq(uN[4]:12, x)
}
```

**Map Built-In** The `map` built-in can map a function over every element in an array to produce the transformed array. Unlike in Rust, functions must be defined at module scope, and in define-before-use order -- there are no lambdas/closures:

```dslx
fn add_one<N: u32>(e: uN[N]) -> uN[N] { e + uN[N]:1 }

#[test]
fn show_map() {
    let x = u4[4]:[0, 1, 2, 3];
    let y = map(x, add_one);
    assert_eq(y, u4[4]:[1, 2, 3, 4]);
}
```

**Match Construct** Pattern matching in DSLX is similar to Rust's, it just supports a subset of patterns that Rust supports. Prefer to use match expressions instead of if/else ladders. Tuples and constants can notably be pattern matched on:

```dslx
#[test]
fn show_match() {
    let my_tuple = (u32:42, u8:64);
    let result = match my_tuple {
        (u32:42, _) => u32:42,  // _ is wildcard matcher
        (first, u8:64) => {  // match expression can be a block
            first + u32:1
        },
        // DSLX can not determine exhaustiveness of patterns so a trailing wildcard is always necessary
        // When the arm is effectively unreachable we can use the `fail!` built-in.
        // Note the first argument to fail must be a valid Verilog identifier.
        _ => fail!("first_should_match", u32:0)
    };
    assert_eq(result, u32:42)
}
```

That is all of the tutorial content.

---

Q: Now try to write an LFSR implementation in DSLX. Make it parameterized on number of bits, bitmask for taps, and whether we invert the feedback bit.
