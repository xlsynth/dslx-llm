# CRC16 Update

## Prompt

Implement one byte update for CRC-16/CCITT-FALSE.

Parameters:

- Width: 16 bits
- Polynomial: `0x1021`
- Input processing: non-reflected, most-significant bit first
- Per-byte update: XOR the input byte into the high byte of the current CRC,
  then perform 8 polynomial steps
- Final XOR: none

This function updates an already-running CRC value with one additional byte; it
does not choose the initial value.

The prologue will be automatically included, just implement the signature in
the output answer.

## Signature

```dslx-snippet
fn crc16_update(crc: u16, data: u8) -> u16
```

## Tests

```dslx-snippet
fn crc16_update_ascii_123456789(init: u16) -> u16 {
    let c0 = crc16_update(init, u8:0x31);
    let c1 = crc16_update(c0, u8:0x32);
    let c2 = crc16_update(c1, u8:0x33);
    let c3 = crc16_update(c2, u8:0x34);
    let c4 = crc16_update(c3, u8:0x35);
    let c5 = crc16_update(c4, u8:0x36);
    let c6 = crc16_update(c5, u8:0x37);
    let c7 = crc16_update(c6, u8:0x38);
    crc16_update(c7, u8:0x39)
}

#[test]
fn test_crc16_update_single_byte_vectors() {
    assert_eq(crc16_update(u16:0x0000, u8:0x00), u16:0x0000);
    assert_eq(crc16_update(u16:0xffff, u8:0x00), u16:0xe1f0);
    assert_eq(crc16_update(u16:0xffff, u8:0x31), u16:0xc782);
    assert_eq(crc16_update(u16:0x0000, u8:0x31), u16:0x2672);
    assert_eq(crc16_update(u16:0x1234, u8:0xab), u16:0x02f2);
}

#[test]
fn test_crc16_update_standard_check_strings() {
    assert_eq(crc16_update_ascii_123456789(u16:0xffff), u16:0x29b1);
    assert_eq(crc16_update_ascii_123456789(u16:0x0000), u16:0x31c3);
}

#[quickcheck]
fn prop_crc16_update_is_linear(crc_a: u16, crc_b: u16, data_a: u8, data_b: u8) -> bool {
    crc16_update(crc_a ^ crc_b, data_a ^ data_b) ==
        (crc16_update(crc_a, data_a) ^ crc16_update(crc_b, data_b))
}

#[quickcheck(exhaustive)]
fn prop_zero_crc_zero_data_stays_zero(_: u1) -> bool {
    crc16_update(u16:0, u8:0) == u16:0
}
```
