import pytest
import cluster as C


def test_tach_speedo_fuel():
    assert C.tach_frame(0x12, 0x34) == bytes.fromhex("881B10101234")
    assert C.speedo_frame(0x56, 0x78) == bytes.fromhex("88291002" "5678")
    assert C.fuel_frame(0xFF) == bytes.fromhex("8AEA400280FF")


def test_odometer_roundtrip():
    for v in (0, 1, 12345, 999_999, C.ODO_MAX):
        f = C.odo_frame(v)
        assert f[:4] == bytes.fromhex("C87B4001") and len(f) == 8
        assert C.decode_odo(f) == v
    # raw = value * 103, big-endian
    assert C.odo_frame(1)[4:] == (103).to_bytes(4, "big")


def test_range_checks():
    with pytest.raises(ValueError):
        C.tach_frame(256, 0)
    with pytest.raises(ValueError):
        C.odo_frame(C.ODO_MAX + 1)
    with pytest.raises(ValueError):
        C.odo_frame(-1)


def test_coolant_frame():
    assert C.coolant_frame(0x55) == bytes.fromhex("8AEA400281" "55")


def test_decode_roundtrip_with_and_without_crc():
    cases = [
        (C.tach_frame(0x1F, 0x40), ("rpm", 0x1F40)),
        (C.speedo_frame(0x03, 0x80), ("speed", 0x0380)),
        (C.fuel_frame(0xC8), ("fuel", 0xC8)),
        (C.coolant_frame(0x7F), ("coolant", 0x7F)),
        (C.odo_frame(123456), ("odo", 123456 * 103)),
    ]
    for frame, expected in cases:
        assert C.decode_frame(frame) == expected
        assert C.decode_frame(frame + b"\xAB") == expected      # trailing CRC ignored


def test_decode_rejects_other_frames():
    assert C.decode_frame(bytes.fromhex("6CFEF028 00F0".replace(" ", ""))) is None
    assert C.decode_frame(bytes.fromhex("881B1010")) is None       # truncated
    assert C.decode_frame(b"") is None


def test_default_scalings():
    assert round(C.DEFAULT_SCALING["fuel"].apply(255), 3) == 100.0
    assert round(C.DEFAULT_SCALING["rpm"].apply(0x1F40), 1) == 2000.0


def test_coolant_piecewise_passes_through_measured_points():
    pts = C.DEFAULT_COOLANT_POINTS
    for raw, temp in pts:
        assert C.piecewise(raw, pts) == pytest.approx(temp)
    # between points: linear
    assert C.piecewise(98.5, pts) == pytest.approx((147.5 + 195.0) / 2)
    # extrapolation follows the end segments and stays monotonic
    assert C.piecewise(0, pts) < 147.5 and C.piecewise(255, pts) > 227.5
    assert C.piecewise(255, pts, extrapolate=False) == 227.5


def test_points_valid_and_dial_ticks():
    assert C.points_valid(C.DEFAULT_COOLANT_POINTS)
    assert not C.points_valid([(69, 147.5), (69, 195.0)])        # duplicate raw
    assert not C.points_valid([(69, 200.0), (128, 195.0)])       # temp goes down
    ticks = C.coolant_dial_ticks(C.DEFAULT_COOLANT_POINTS)
    assert ticks == [(100.0, 0.0), (147.5, 0.25), (195.0, 0.5), (227.5, 0.75), (260.0, 1.0)]
