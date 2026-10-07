import struct
import protocol as P


def feed_all(parser, data):
    return parser.feed(data)


def test_build_frames():
    assert P.build_frame(0x49) == bytes([2, 1, 0x49, 3])
    assert P.build_rx_mode_frame(True) == bytes([2, 2, 1, 1, 3])
    assert P.build_send_frame(bytes([0x6C, 0xFE])) == bytes([2, 3, 2, 0x6C, 0xFE, 3])


def test_parse_hex():
    assert P.parse_hex("68 6A F1") == bytes([0x68, 0x6A, 0xF1])
    assert P.parse_hex("686af1") == bytes([0x68, 0x6A, 0xF1])
    assert P.parse_hex("0x68, 0x6A") == bytes([0x68, 0x6A])
    assert P.parse_hex("6") is None
    assert P.parse_hex("ZZ") is None
    assert P.parse_hex("  ") is None


def test_ack_nack_identify():
    p = P.FrameParser()
    frames = p.feed(bytes([2, 1, 6, 3, 2, 1, 0x15, 3, 2, 2, 6, 0x4A, 3]))
    assert [f.kind for f in frames] == ["ACK", "NACK", "IDENTIFY"]


def test_rx_frame_and_trim():
    raw = bytes([2, 7, 0x10, 0x02, 0, 0, 0x80, 0x3F, 0xAA, 3])
    p = P.FrameParser()
    (f,) = p.feed(raw)
    assert f.kind == "RX" and f.data == bytes([2, 0, 0, 0x80, 0x3F, 0xAA])
    p.trim_crc = True
    (f,) = p.feed(raw)
    assert f.data == bytes([2, 0, 0, 0x80, 0x3F])


def test_split_chunks_and_resync():
    p = P.FrameParser()
    out = []
    for b in bytes([0xFF, 0xFF, 2, 1, 6, 3]):      # junk then ACK, byte by byte
        out += p.feed(bytes([b]))
    assert [f.kind for f in out] == ["ACK"]
    # bad ETX followed by a good frame
    out = p.feed(bytes([2, 1, 6, 0x99, 2, 1, 6, 3]))
    assert [f.kind for f in out] == ["ACK"]


def test_datapoints_roundtrip():
    fl = P.DATAPOINTS_BY_ID[0x02]
    raw = P.encode_value(fl, "1.5")
    assert raw == struct.pack("<f", 1.5) and P.decode_value(fl, raw) == "1.5000"
    u = P.DATAPOINTS_BY_ID[0x06]
    assert P.decode_value(u, P.encode_value(u, "12345")) == "12345"
    for bad in ("-1", "abc", "4294967296"):
        try:
            P.encode_value(u, bad)
            assert False
        except ValueError:
            pass
    assert P.build_write(fl, raw)[:2] == bytes([0x99, 0x02])


def test_playback_parser():
    res = P.parse_playback(["# c", "*100", "6C FE F0", "*250", "68 6A F1", "zz", "*bad", "// x", ""])
    assert [(f.data.hex(), f.delay_ms) for f in res.frames] == [("6cfef0", 100), ("686af1", 250)]
    assert res.skipped == 1
