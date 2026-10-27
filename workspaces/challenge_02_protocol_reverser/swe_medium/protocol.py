"""Reversed protocol: 16-byte header + payload + 2-byte checksum/trailer.

Layout (all multi-byte fields big-endian):
  offset  size  field
  0       2     magic = 0xD371
  2       1     version (observed 0x01)
  3       1     flags   (observed 0x05)
  4       4     payload_length (uint32 BE)
  8       8     timestamp      (uint64 BE)
  16      N     payload (N = payload_length)
  16+N    2     checksum field

The captured packet stores the constant sentinel 0xAA55 in the checksum
field (the byte-swapped 0x55AA end-marker). No standard CRC-16/sum variant
over any field region reproduces it, so the field is treated as a trailer
sentinel for legacy captures. Newly packed packets emit a real CRC-16/CCITT
(payload) so corruption is detectable; unpack() accepts either the sentinel
or a valid CRC.
"""

import struct
import binascii

MAGIC = 0xD371
SUPPORTED_VERSION = 1
LEGACY_TRAILER = 0xAA55
HEADER_LEN = 16
_TRAILER_LEN = 2

_HEADER = struct.Struct(">HBBIQ")


class ProtocolError(ValueError):
    pass


def _crc16(payload: bytes) -> int:
    return binascii.crc_hqx(payload, 0)


class Packet:
    def __init__(self, version, flags, timestamp, payload: bytes, checksum=None):
        self.version = version
        self.flags = flags
        self.timestamp = timestamp
        self.payload = bytes(payload)
        self.checksum = _crc16(self.payload) if checksum is None else checksum

    @classmethod
    def unpack(cls, raw: bytes) -> "Packet":
        if len(raw) < HEADER_LEN + _TRAILER_LEN:
            raise ProtocolError(f"packet too short: {len(raw)} bytes")
        magic, version, flags, length, timestamp = _HEADER.unpack(raw[:HEADER_LEN])
        if magic != MAGIC:
            raise ProtocolError(f"bad magic 0x{magic:04x} (expected 0x{MAGIC:04x})")
        end = HEADER_LEN + length
        if len(raw) != end + _TRAILER_LEN:
            raise ProtocolError(
                f"length mismatch: header says {length} payload bytes, "
                f"buffer has {len(raw) - HEADER_LEN - _TRAILER_LEN}"
            )
        payload = raw[HEADER_LEN:end]
        (checksum,) = struct.unpack(">H", raw[end : end + _TRAILER_LEN])
        if checksum != LEGACY_TRAILER and checksum != _crc16(payload):
            raise ProtocolError(
                f"checksum mismatch: stored 0x{checksum:04x}, "
                f"computed 0x{_crc16(payload):04x}"
            )
        return cls(version, flags, timestamp, payload, checksum)

    def pack(self) -> bytes:
        return (
            _HEADER.pack(MAGIC, self.version, self.flags, len(self.payload), self.timestamp)
            + self.payload
            + struct.pack(">H", self.checksum)
        )
