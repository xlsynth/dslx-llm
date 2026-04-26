# Hamming Correct

## Prompt

Implement a systematic extended Hamming(8,4) encoder and single-error corrector.

The codeword layout is LSB-zero:

- bits `0..3`: message bits `m0..m3`
- bit `4`: parity `p0 = m0 ^ m1 ^ m3`
- bit `5`: parity `p1 = m0 ^ m2 ^ m3`
- bit `6`: parity `p2 = m1 ^ m2 ^ m3`
- bit `7`: overall parity over bits `0..6`

The corrector must:

- return the decoded message bits from the corrected codeword when correction
  succeeds
- report `corrected = false` and `uncorrectable = false` for a clean codeword
- correct any single-bit error, including the overall parity bit, and report
  `corrected = true`, `uncorrectable = false`
- detect any double-bit error and report `corrected = false`,
  `uncorrectable = true`
- for uncorrectable inputs, leave the received codeword unchanged in
  `corrected_codeword` and return its low four bits as `message`

The prologue will be automatically included, just implement the signature in
the output answer.

## Prologue

```dslx
struct Hamming84Result {
    message: u4,
    corrected_codeword: u8,
    corrected: bool,
    uncorrectable: bool,
}
```

## Signature

```dslx-snippet
fn hamming84_encode(message: u4) -> u8
fn hamming84_correct(received: u8) -> Hamming84Result
```

## Tests

```dslx-snippet
#[test]
fn test_hamming84_encode_table() {
    const CASES = [
        (u4:0x0, u8:0x00),
        (u4:0x1, u8:0xb1),
        (u4:0x2, u8:0xd2),
        (u4:0x3, u8:0x63),
        (u4:0x4, u8:0xe4),
        (u4:0x5, u8:0x55),
        (u4:0x6, u8:0x36),
        (u4:0x7, u8:0x87),
        (u4:0x8, u8:0x78),
        (u4:0x9, u8:0xc9),
        (u4:0xa, u8:0xaa),
        (u4:0xb, u8:0x1b),
        (u4:0xc, u8:0x9c),
        (u4:0xd, u8:0x2d),
        (u4:0xe, u8:0x4e),
        (u4:0xf, u8:0xff),
    ];
    for ((message, want), ()) in CASES {
        assert_eq(hamming84_encode(message), want);
    }(());
}

#[test]
fn test_hamming84_correct_clean_and_specific_errors() {
    let clean = hamming84_correct(u8:0x55);
    assert_eq(clean, Hamming84Result {
        message: u4:0x5,
        corrected_codeword: u8:0x55,
        corrected: false,
        uncorrectable: false,
    });

    let data_error = hamming84_correct(u8:0x55 ^ u8:0x01);
    assert_eq(data_error, Hamming84Result {
        message: u4:0x5,
        corrected_codeword: u8:0x55,
        corrected: true,
        uncorrectable: false,
    });

    let overall_parity_error = hamming84_correct(u8:0x55 ^ u8:0x80);
    assert_eq(overall_parity_error, Hamming84Result {
        message: u4:0x5,
        corrected_codeword: u8:0x55,
        corrected: true,
        uncorrectable: false,
    });

    let double_error = hamming84_correct(u8:0x55 ^ u8:0x03);
    assert_eq(double_error, Hamming84Result {
        message: u4:0x6,
        corrected_codeword: u8:0x56,
        corrected: false,
        uncorrectable: true,
    });
}

#[quickcheck(exhaustive)]
fn quickcheck_clean_codewords_decode(message: u4) -> bool {
    let codeword = hamming84_encode(message);
    hamming84_correct(codeword) == Hamming84Result {
        message,
        corrected_codeword: codeword,
        corrected: false,
        uncorrectable: false,
    }
}

#[quickcheck(exhaustive)]
fn quickcheck_all_single_bit_errors_correct(message: u4, pos: u3) -> bool {
    let codeword = hamming84_encode(message);
    let received = bit_slice_update(codeword, pos as u32, !codeword[pos as u32 +: u1]);
    hamming84_correct(received) == Hamming84Result {
        message,
        corrected_codeword: codeword,
        corrected: true,
        uncorrectable: false,
    }
}

#[quickcheck(exhaustive)]
fn quickcheck_double_bit_errors_detected(message: u4, pos0: u3, pos1: u3) -> bool {
    if pos0 < pos1 {
        let codeword = hamming84_encode(message);
        let flipped0 = bit_slice_update(codeword, pos0 as u32, !codeword[pos0 as u32 +: u1]);
        let received = bit_slice_update(flipped0, pos1 as u32, !flipped0[pos1 as u32 +: u1]);
        let got = hamming84_correct(received);
        !got.corrected && got.uncorrectable && got.corrected_codeword == received
    } else {
        true
    }
}
```
