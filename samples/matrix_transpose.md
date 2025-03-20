# Matrix Transpose

## Prompt

It is useful to rearrange data stored in multi-dimensional arrays. Write a routine to transpose a `M`x`N` matrix of `B`-bit values.

## Signature

```dslx-snippet
fn matrix_transpose<M: u32, N: u32, B: u32>(x: uN[B][M][N]) -> uN[B][N][M]
```

## Tests

```dslx-snippet
#[test]
fn test_transpose_3x2() {
    // Define a concrete 3x2 matrix:
    let m = u8[2][3]:[
        [u8:1, u8:2],
        [u8:3, u8:4],
        [u8:5, u8:6]
    ];
    // Its expected transpose (u8[3][2]) is:
    // [ [1, 3, 5],
    //   [2, 4, 6] ]
    let expected = u8[3][2]:[
        [u8:1, u8:3, u8:5],
        [u8:2, u8:4, u8:6]
    ];
    let got: u8[3][2] = matrix_transpose(m);
    assert_eq(got, expected);
}

#[quickcheck]
fn quickcheck_transpose_involution(a: u8[2][3]) -> bool {
    // Verify that transposing twice yields the original matrix.
    // That is, transpose_3x2(transpose_3x2(a)) == a.
    let t: u8[3][2] = matrix_transpose(a);
    let tt: u8[2][3] = matrix_transpose(t);
    tt == a
}
```
