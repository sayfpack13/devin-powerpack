# Challenge 02: Binary Protocol Reverse Engineering & Parser

## Objective
Analyze an unknown binary packet capture (`sample_capture.bin`), reverse-engineer the header structure, field offsets, and payload encoding, and construct a robust parser and validator.

## Instructions:
Paste the prompt below into Devin chat:

```markdown
Initialize this clean workspace using devin-state-init.

We captured a raw binary packet in `sample_capture.bin`. 
Use the reverse_engineer subagent and Mythos v3.0 reverse engineering protocols:

1. Reverse-Engineer the Binary Layout:
   - Do NOT dump raw bytes into context. Use python or hex inspection to extract field offsets.
   - Identify header fields: Magic bytes, Version, Flags, Payload Length, 64-bit Timestamp, and trailing Checksum.
   - Document the protocol schema in `.mythos/re_symbols.md`.
2. Construct Parser & Serializer:
   - Build `protocol.py` with `Packet.unpack(raw_bytes)` and `Packet.pack()`.
   - Validate magic bytes and payload checksum.
3. Automated Testing & Verification:
   - Write `test_protocol.py` testing serialization, deserialization, invalid magic byte handling, and corrupt payload rejection.
   - Run tests and provide exact exit code 0 evidence.
```
