# Error-Correcting Code

## Prompt

Write an error-correcting code that implements a single-error-correcting, double-error-detecting (SECDED) behavior for a K-bit message.
You are free to decide the code construction, as long as the code is in systematic form and codewords are N = K + R bits long, where R is the number of parity bits.
Systematic form means codewords are encoded by concatenating the message with the generated parity bits.

Codewords may be corrupted by bit flips outside of your control.
The SECDED code must correct all single-bit flips, detect (but not correct) all double-bit flips, and either detect or attempt to correct all triple-bit flips (they cannot go undetected).

Your task is to design the code construction and implement the encoder and decoder pair for that construction.
You do not control the channel between the encoder and decoder, i.e., you will never be told whether any bits are flipped, nor their potential locations.

You only need to implement for the following code parameters:
* K = 64
* R = 8
* N = 72

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
// Instance parameters for the (72,64) SECDED code.
const K = u32:64;
const R = u32:8;
const N = K + R;
```

## Signature

```dslx-snippet
// Encodes a K-bit message into an N-bit codeword in systematic form.
fn ecc_encoder(message: bits[K]) -> bits[N]

// Decodes an N-bit received codeword, corrects single-bit errors, detects double errors.
fn ecc_decoder(received: bits[N]) -> (bits[K], bool, bool)
```

## Tests

```dslx-snippet
// Tests the encoder and decoder without any injected errors.
#[quickcheck]
fn quickcheck_no_errors(message: bits[K]) -> bool {
    let codeword = ecc_encoder(message);
    let (decoded_message, ce, due) = ecc_decoder(codeword);
    !ce && !due && message == decoded_message
}

// Tests that all single-bit errors are corrected.
#[quickcheck]
fn quickcheck_single_bit_error_correction(message: bits[K], pos: u32) -> bool {
    let codeword = ecc_encoder(message);
    if pos < N {
        let received_codeword = bit_slice_update(codeword, pos, (!codeword[pos +: u1]) as u1);
        let (decoded_message, ce, due) = ecc_decoder(received_codeword);
        ce && !due && decoded_message == message
    } else {
        true
    }
}

// Tests that all double-bit errors are detected.
#[quickcheck]
fn quickcheck_double_bit_error_detection(message: bits[K], pos0: u32, pos1: u32) -> bool {
    let codeword = ecc_encoder(message);
    if pos0 < N && pos1 < N && pos0 < pos1 {
        let flipped0 = bit_slice_update(codeword, pos0, (!codeword[pos0 +: u1]) as u1);
        let received_codeword = bit_slice_update(flipped0, pos1, (!flipped0[pos1 +: u1]) as u1);
        let (_, ce, due) = ecc_decoder(received_codeword);
        !ce && due
    } else {
        true
    }
}

// Tests that all triple-bit errors are detected. They may sometimes be corrected or miscorrected, but
// must not be silently undetected.
#[quickcheck]
fn quickcheck_triple_bit_error_not_undetected(message: bits[K], pos0: u32, pos1: u32, pos2: u32) -> bool {
    let codeword = ecc_encoder(message);
    if pos0 < N && pos1 < N && pos2 < N && pos0 < pos1 && pos1 < pos2 {
        let flipped0 = bit_slice_update(codeword, pos0, (!codeword[pos0 +: u1]) as u1);
        let flipped1 = bit_slice_update(flipped0, pos1, (!flipped0[pos1 +: u1]) as u1);
        let received_codeword = bit_slice_update(flipped1, pos2, (!flipped1[pos2 +: u1]) as u1);
        let (_, ce, due) = ecc_decoder(received_codeword);
        ce || due
    } else {
        true
    }
}

// Tests that the code is in systematic form (first K bits of the encoded codeword match the message).
#[quickcheck]
fn quickcheck_systematic(message: bits[K]) -> bool {
    let codeword = ecc_encoder(message);
    message == codeword[0 +: uN[K]]
}
```
