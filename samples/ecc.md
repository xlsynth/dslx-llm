# Error-Correcting Code

## Prompt

Write an error-correcting code that implements a single-error-correcting, double-error-detecting (SECDED) behavior for a K=64-bit message.
You are free to decide the code construction, including the number of parity bits (R), with the requirement that the code is in systematic form.
A codeword is N = K + R bits long and is formed by concatenating the message with the generated parity bits.

Codewords may be corrupted by bit flips outside of your control.
The SECDED code must correct all single-bit flips, detect (but not correct) all double-bit flips, and either detect or attempt to correct all triple-bit flips.

Your task is to design the code construction and implement the encoder and decoder pair for that construction.
You do not control the channel between the encoder and decoder, i.e., you will never be told whether any bits are flipped, nor their potential locations.

The prologue will be automatically included, just implement the signature in the output answer.

## Prologue

```dslx
```

## Signature

```dslx-snippet
// Encodes a K-bit message into an N-bit codeword.
fn ecc_encoder<K: u32>(message: bits[K]) -> (bits[N])

// Decodes an N-bit received codeword into a tuple:
// * K-bit message
// * 1-bit corrected error (CE) flag
// * 1-bit detected-but-uncorrectable error (DUE) flag
//
// The CE and DUE flags are mutually exclusive.
fn ecc_decoder<N: u32>(received_codeword: bits[N]) -> (bits[K], bool, bool)
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
```
