import unittest
from pathlib import Path

from protocol import Packet, ProtocolError, MAGIC, LEGACY_TRAILER, HEADER_LEN

SAMPLE = "sample_capture.bin"
PAYLOAD = b"SECRET_INTERNAL_SESSION_TOKEN_XYZ987"
TS = 0x6AE0B514


class TestProtocol(unittest.TestCase):
    def test_unpack_sample_capture(self):
        raw = Path(SAMPLE).read_bytes()
        p = Packet.unpack(raw)
        self.assertEqual(p.version, 1)
        self.assertEqual(p.flags, 5)
        self.assertEqual(p.timestamp, TS)
        self.assertEqual(p.payload, PAYLOAD)
        self.assertEqual(p.checksum, LEGACY_TRAILER)

    def test_roundtrip_pack_unpack(self):
        p = Packet(version=1, flags=0x05, timestamp=TS, payload=PAYLOAD)
        q = Packet.unpack(p.pack())
        self.assertEqual((q.version, q.flags, q.timestamp, q.payload),
                         (p.version, p.flags, p.timestamp, p.payload))
        self.assertEqual(q.checksum, p.checksum)

    def test_empty_payload_roundtrip(self):
        p = Packet(version=1, flags=0, timestamp=0, payload=b"")
        self.assertEqual(Packet.unpack(p.pack()).payload, b"")

    def test_invalid_magic_rejected(self):
        raw = bytearray(Path(SAMPLE).read_bytes())
        raw[0] ^= 0xFF
        with self.assertRaises(ProtocolError):
            Packet.unpack(bytes(raw))

    def test_corrupt_payload_rejected(self):
        p = Packet(version=1, flags=5, timestamp=TS, payload=PAYLOAD)
        raw = bytearray(p.pack())
        raw[HEADER_LEN] ^= 0xFF  # flip a payload bit; stored CRC no longer matches
        with self.assertRaises(ProtocolError):
            Packet.unpack(bytes(raw))

    def test_truncated_packet_rejected(self):
        raw = Path(SAMPLE).read_bytes()
        with self.assertRaises(ProtocolError):
            Packet.unpack(raw[:-1])
        with self.assertRaises(ProtocolError):
            Packet.unpack(raw[:10])

    def test_trailing_garbage_rejected(self):
        raw = Path(SAMPLE).read_bytes() + b"\x00"
        with self.assertRaises(ProtocolError):
            Packet.unpack(raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
