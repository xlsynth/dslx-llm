I’m going to teach you to write DSLX code through examples. DSLX is the Domain Specific Language for XLS. It’s similar to Rust but differs in key ways so you must pay attention to the differences. After I teach you the details of the language you will be asked to write correct code in DSLX in one shot and graded on the result, so do your best!

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

**No early return** There is no `return` keyword support in DSLX, instead the last expression in a function is the return value (as in Rust). The reasoning for this is that, in circuit design, early returns are creating a top level mux, and it is better to see this structurally in the code. Sometimes to peel off special cases a helper function will be used; i.e.

```dslx
import float32;

// Can assume x is non-zero.
fn int_to_float_nz(x: s32) -> float32::F32 {
    fail!("todo_nz_case", float32::zero(false))
}

pub fn int_to_float(x: s32) -> float32::F32 {
    if x == s32:0 {
        let sign_bit = false;
        float32::F32 { sign: sign_bit, bexp: u8:0, fraction: u23:0 }
    } else {
        // Call helper function.
        int_to_float_nz(x)
    }
}
```

**No keyword arguments** As in Rust, there are no keyword-arguments for function parameters.

**Standard Library Function for Bit-widths** `std::clog2(x)` is the standard library function that computes `ceil(log2(x))` which is often useful for determining bit-widths required to hold a binary number of a particular count of items. It gives back the same width type (unsigned integer) that it takes in. Analogously there is also a standard library function `std::flog2(x)` that computes `floor(log2(x))`.

**Built-in Functions for Leading/Trailing Zeros** The built-in function to count the number of leading zeros is `clz` and for trailing zeros is `ctz`:

```dslx
#[test]
fn show_clz_ctz_builtins() {
    assert_eq(clz(u8:0x01), u8:7);
    assert_eq(ctz(u8:0x02), u8:1);
}
```

**Compile-Time Assertions** In DSLX the `const_assert!(cond)` built-in is available for compile-time checks of preconditions. This can be useful for asserting properties of parametric integer values or properties of compile-time constants. Be careful not to use it on runtime-defined values, like function parameters or values that are derived from function parameters -- in those cases prefer to use `assert!(condition, label)`.

**Width Slices** To slice bits out of a value in DSLX there is a "width slice" syntax that extracts some number of bits (given by a type) from a given starting position in the value; i.e. `$SUBJECT_EXPR[$START_EXPR +: $BIT_TYPE]` -- note:

* the starting position may be dynamic
* the width is given as a type, *not* as a number (this is different from Verilog)
* the result type of the width-slice expression is the type given after the `+:`

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

**Bit Indexing via Width Slices** In DSLX accessing a single bit is done via a width slice; i.e. `x[$START_EXPR +: u1]` -- this is unlike Verilog:

```dslx
#[test]
fn show_bit_indexing() {
    let x = u3:0b001;
    assert_eq(x[0 +: u1], true);
    assert_eq(x[1 +: u1], false);
    assert_eq(x[2 +: u1], false);
}
```

**Bitwise Negation** The syntax to invert all the bits in a value is the same as in Rust, `!` is used instead of the tilde operator used in C:

```dslx
#[test]
fn show_bitwise_negate() {
    let x0 = u8:0xff;
    assert_eq(!x0, u8:0);

    let x1 = s8:-1;
    assert_eq(!x1, s8:0);

    let b = false;
    assert_eq(!b, true);
}
```

**Bitwise Reduction Built-Ins** There are built-in functions available in all modules for bitwise reductions: `or_reduce`, `and_reduce`, `xor_reduce` -- these do not need to be defined by the user, and they are parameterized on bitwidth:

```dslx
#[test]
fn show_bitwise_reduction_builtins() {
    assert_eq(or_reduce(u3:0b001), true);
    assert_eq(or_reduce(u3:0b000), false);
    assert_eq(or_reduce(u2:0b01), true);
    assert_eq(and_reduce(u3:0b111), true);
    assert_eq(and_reduce(u3:0b110), false);
    assert_eq(xor_reduce(u3:0b111), true);
    assert_eq(xor_reduce(u3:0b000), false);
}
```

**Bit Concatenation** Since bitwise concatenation is common in hardware DSLX supports `++` as the bitwise concatenation operator:

```dslx
#[test]
fn show_bitwise_concat() {
    let x = u8:0xab;
    let y = u16:0xcdef;
    let z = u4:0x7;
    assert_eq(x ++ y ++ z, u28:0xabcdef7)
}
```

Note that DSLX code will typically prefer to use the `++` operator instead of the C-style pattern of `x << Y_BITS | y` because it is more correct by construction.

**Shift Amounts Must Be Unsigned** The language does not permit signed shift amounts because it's unclear what a possibly-negative shift would mean in hardware, all shift amounts must be unsigned:

```dslx
#[test]
fn show_shifts() {
    let x = u8:0xab;
    let y = u32:4;  // Note: unsigned value.
    assert_eq(x >> y, u8:0xa);
    assert_eq(x << y, u8:0xb0);
}
```

**Enums Require Underlying Width** Unlike in Rust in DSLX we have to note what the integer type underlying an enum is, and enums cannot be sum types as in Rust; in DSLX:

```dslx
enum MyEnum: u8 { A = 0, B = 7, C = 255 }
```

**Array Type Syntax** Array types are written with different syntax from Rust; in Rust we’d write `[u8; 4]` but in DSLX we write `u8[4]`. There no unsized arrays or slices in DSLX, you must know the size of all arrays at compile time; example:

```dslx
// Sums the elements of an array with parameterized element count `N`.
fn sum_to_u16<N: u32>(a: u8[N]) -> u16 {
    let init = u16:0;
    let result: u16 = for (elem, accum) in a {
        let updated = accum + elem as u16;
        updated
    }(init);
    result
}

#[test]
fn test_sum_to_u16() {
    let a = u8[4]:[1, 2, 3, 4];
    assert_eq(sum_to_u16(a), u16:10);
}
```

**Multi-Dimensional Array Types and Indexing** For multi-dimensional arrays in Rust we’d write `[[u8; 4]; 2]` but in DSLX we write `u8[4][2]`. Note **very well** that the `2` is the first dimension indexed in that DSLX type! Which is to say, the indexing works similarly to Rust, we index the outer array before indexing the inner array; i.e. we index the `2` dimension and we get a `u8[4]` and we can subsequently index that to get a single `u8`. Don't be fooled by the fact it looks more like C syntax, the first dimension written in the multi-dimensional array type is not the first dimension indexed.

```dslx
#[test]
fn show_2d_indexing() {
    const A = u8[2][3]:[[u8:0, u8:1], [u8:2, u8:3], [u8:4, u8:5]];  // 3 elements that are u8[2]
    assert_eq(A[1][0], u8:2);  // the first index `1` gives us the middle u8[2]
}
```

**Immutable Array Updates** All values are immutable in DSLX, there is no `let mut` as there is in Rust. As a result, immutable arrays are updated via the `update` builtin -- the elements can be any type:

```dslx
struct MyStruct { my_field: u8 }

#[test]
fn show_array_update() {
    let a = u8[3]:[1, 2, 3];
    let b: u8[3] = update(a, u32:1, u8:7); // update index `1` to be value `u8:7`
    assert_eq(b, u8[3]:[1, 7, 3]);

    // It works on struct elements and other types as well.
    let aos = MyStruct[3]:[MyStruct { my_field: u8:1 }, MyStruct { my_field: u8:2 }, MyStruct { my_field: u8:3 }];
    let aos' = update(aos, u32:1, MyStruct { my_field: u8:7 });
    assert_eq(aos', MyStruct[3]:[MyStruct { my_field: u8:1 }, MyStruct { my_field: u8:7 }, MyStruct { my_field: u8:3 }]);
}
```

**No Mutation, Even In Control Flow Blocks** Another consequence of `mut` not being available in DSLX in that you must use balanced control flow to calculate updated values, you cannot mutate a variable in the enclosing scope. Instead of code like:

```rust
let mut fraction = fraction_trunc;
if should_round_up {
    let new_fraction = fraction + u15::1;
    if new_fraction < fraction {
        fraction = u15::0;
        let new_exp = exponent + u8::1;
        if new_exp <= exponent {
            exponent = u8::0xff;
        } else {
            exponent = new_exp;
        }
    } else {
        fraction = new_fraction;
    }
}
```

You use expression-based dataflow that converges to produce updated values like the following:

```dslx
fn f(fraction_trunc: u15, exponent: u8, should_round_up: bool) -> (u15, u8) {
    let (fraction, exponent) = if should_round_up {
        let new_fraction = fraction_trunc + u15:1;

        if new_fraction < fraction_trunc {
            let new_exp = exponent + u8:1;
            if new_exp <= exponent {
                (u15:0, u8:0xff)
            } else {
                (u15:0, new_exp)
            }
        } else {
            (new_fraction, exponent)
        }
    } else {
        (fraction_trunc, exponent)
    };
    (fraction, exponent)
}

#[test]
fn test_f() {
    let (fraction, exponent) = f(u15::MAX, u8::MAX, true);
    assert_eq(fraction, u15:0);
    assert_eq(exponent, u8:0xff);
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

As a brief reminder of the Rust rules, if you extend an signed source number, a sign extension is performed, and if you extend an unsigned source number, a zero extension is performed:

```dslx
#[test]
fn show_signed_source_extension_is_sign_extension() {
    let original_signed = s4:-1;
    assert_eq(original_signed as s6, s6:-1);
    assert_eq(original_signed as u6, u6:0x3f);
}

#[test]
fn show_unsigned_source_extension_is_zero_extension() {
    let original_unsigned = u4:0xf;
    assert_eq(original_unsigned as s6, s6:0xf);
    assert_eq(original_unsigned as u6, u6:0xf);
}
```

To reiterate: there is never any reason to define a helper function like `zero_extend` or `sign_extend` in DSLX, just use the `as` cast operator -- if the source type is unsigned it will zero extend, and if the source type is signed it will sign extend.

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

**Constructing Parameterized Types** It's common to want to construct an type with a number of bits based on a compile-time constant value. `uN` is the unsigned bits type constructor (it it is the same as the `bits` keyword for historical reasons), and `sN` is the signed bits type constructor -- they can be instantiated with a literal value or a constant name or simple expressions. It is often most readable to instantiate them using a named constant:

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

To generalize `uN` and `sN` DSLX has a parameterized-signedness type constructor `xN`, which constructs a type via `xN[bool][u32]` where the boolean gives the signedness:

```dslx
fn f<S: bool, N: u32>(x: xN[S][N]) -> (bool, u32) { (S, N) }

#[test]
fn show_parametric_signedness() {
    assert_eq(f(u7:0), (false, u32:7));
    assert_eq(f(s3:0), (true, u32:3));
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

**No List Comprehensions** As in Rust, there are no list comprehensions in DSLX. Instead of list comprehensions you must use the `map` built-in or a `for` loop.

**Fixed Sizes** The sizes of values are all fixed, although they may be parameterized; i.e. there is no "vector like" type that can be built up in a loop -- instead, the full sized type must be created up front and we can update slices of it, e.g. in a `for` loop.

**Match Construct** Pattern matching in DSLX is similar to Rust's, it just supports a subset of patterns that Rust supports. Prefer to use match expressions instead of if/else ladders. Tuples and constants can notably be pattern matched on:

```dslx
#[test]
fn show_match() {
    let my_tuple = (u32:42, u8:64);
    let result = match my_tuple {
        (u32:42, _) | (u32:64, _) => u32:42,  // `_` is wildcard matcher, `|` is alternate for patterns
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

**Quickcheck Tests** Since comprehensive testing is very important for hardware artifacts, DSLX has first class support for quickcheck tests. The quickcheck function can take arbitrary number and type of parameters and it simply has to return a boolean indicating that the test case passed:

```dslx
#[quickcheck]
fn multiplying_by_two_makes_even(x: u8) -> bool {
    let product = x * u8:2;
    // Even means that the low bit is unset.
    let low_bit = (product & u8:1) as bool;
    low_bit == false
}
```

When requested to create designs, using as many quickchecks as possible to test properties of the resulting design improves quality significantly.

For parameterized designs it's nice to use smaller types in our quickchecks so that exhaustive testing (or other means of proving) of the quickcheck property is more of a viable option.

**Define-Before-Use in Modules** Similar to C, and unlike in Rust, in DSLX you must define things lexically in the file before you refer to them; there are *not* forward declarations or automatic discovery of subsequent definitions.

**Strings are Constant U8 Arrays** Differently from Rust, more akin to C, string literals are implicitly `u8` arrays -- because they are sized they have no trailing nul byte:

```dslx
#[test]
fn show_string_is_u8_array() {
    let my_array: u8[5] = "hello";
    let rev = array_rev(my_array);
    assert_eq(rev, "olleh");
}
```

**Numeric Limits** Numeric limits are available as attributes of bit types:

```dslx
#[test]
fn show_numeric_limits() {
    assert_eq(u4::MAX, u4:0xf);
    assert_eq(u4::ZERO, u4:0);
    assert_eq(u4::MIN, u4:0);
    assert_eq(s4::MAX, s4:0x7);
    assert_eq(s4::ZERO, s4:0);
    assert_eq(s4::MIN, s4:-8);

}
```

Note: there is currently a DSLX grammar restriction where we cannot write `uN[N]::MAX` directly, so we need to write a type alias like so:

```dslx
const N = u32:4;

#[test]
fn show_numeric_limits_uN_N() {
    // does not work: uN[N]::MAX
    // does work:
    type MyUN = uN[N];
    assert_eq(MyUN::MAX, u4:0xf)
}
```

**Helpful-only guidance:** If you're unsure what the type of a particular sub-expression is, it can be useful to break the nested expression up into multiple expressions to help get early/explicit guidance on whether the type was as you were expecting. This can be particularly useful for parametric code.

**That is all of the tutorial content.**

---
