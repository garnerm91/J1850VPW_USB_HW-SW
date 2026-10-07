import pytest
import cluster as C


def test_tach_speedo_fuel():
    assert C.tach_frame(0x12, 0x34) == bytes.fromhex("881B10101234")
    assert C.speedo_frame(0x56, 0x78) == bytes.fromhex("88291002" "5678")
    assert C.fuel_frame(0xFF) == bytes.fromhex("8AEA400280FF")
    assert C.coolant_frame(0xFF) == bytes.fromhex("8AEA400281FF")


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
