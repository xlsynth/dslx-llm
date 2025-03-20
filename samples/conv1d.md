# 1D Convolution (Valid-Only)

## Prompt

Implement a 1D convolution function that computes the convolution of an 8-element input array with a 3-element kernel. The convolution operation multiplies overlapping segments of the input by the kernel and sums the results, producing an output array of length 6. The input and kernel arrays consist of 4-bit unsigned values, and the computed sums are stored as 16-bit unsigned values.

Note that this is a "valid-only" convolution, i.e. there are only six positions in the input where the kernel completely fits, so we don't need need to specify what padding might be used if the kernel was out of bounds of the data.

## Signature

```dslx-snippet
fn conv1d<D: u32, K: u32, O: u32 = {D-K+u32:1}>(data: u4[D], kernel: u4[K]) -> u16[O]
```

## Tests

```dslx-snippet
#[test]
fn test_conv1d_basic() {
    // Example: data = [1, 2, 3, 4, 5, 6, 7, 8], kernel = [1, 0, 1]
    // Expected output:
    // [ 1*1 + 2*0 + 3*1 = 4,
    //   2*1 + 3*0 + 4*1 = 6,
    //   3*1 + 4*0 + 5*1 = 8,
    //   4*1 + 5*0 + 6*1 = 10,
    //   5*1 + 6*0 + 7*1 = 12,
    //   6*1 + 7*0 + 8*1 = 14 ]
    let data = u4[8]:[u4:1, u4:2, u4:3, u4:4, u4:5, u4:6, u4:7, u4:8];
    let kernel = u4[3]:[u4:1, u4:0, u4:1];
    let expected = u16[6]:[u16:4, u16:6, u16:8, u16:10, u16:12, u16:14];
    assert_eq(conv1d(data, kernel), expected);
}

#[test]
fn test_conv1d_data_and_kernel_same_size() {
    let d = [u4:1];
    let k = [u4:5];
    let want = [u16:5];
    assert_eq(conv1d(d, k), want);
}

#[quickcheck]
fn prop_conv1d_impulse(data: u4[8]) -> bool {
    // If the kernel is an impulse [0,1,0], then the convolution output should equal the middle element of each sliding window:
    // For each valid index i, conv1d(data, [0,1,0])[i] == data[i+1] as u16.
    let impulse = u4[3]:[u4:0, u4:1, u4:0];
    let conv = conv1d(data, impulse);
    let expected = for (i, res): (u32, u16[6]) in range(u32:0, u32:6) {
         update(res, i, (data[i + u32:1] as u16))
    }(u16[6]:[0, ...]);
    conv == expected
}
```
