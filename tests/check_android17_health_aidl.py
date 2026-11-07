#!/usr/bin/env python3
"""Offline Android 17 Qualcomm health AIDL source boundary checks.

Source-only: not a Soong compile, device VINTF check, recovery boot or battery test.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    vintf = ET.parse(ROOT / "aidl/android.hardware.health-service.qti.xml").getroot()
    hals = vintf.findall("hal")
    assert vintf.attrib == {"version": "1.0", "type": "device"}
    assert len(hals) == 1, "expected one health HAL declaration"
    hal = hals[0]
    assert hal.attrib.get("format") == "aidl", "legacy HIDL cannot be installed"
    assert hal.findtext("name") == "android.hardware.health"
    assert hal.findtext("version") == "5", "AOSP17 libhealth_aidl_impl_user links V5"
    assert hal.findtext("fqname") == "IHealth/default"

    bp = (ROOT / "aidl/Android.bp").read_text()
    assert '"libhealth_aidl_impl_user"' in bp
    assert '"libhealth_aidl_impl"' in bp
    assert '"android.hardware.health-service.qti"' in bp
    assert '"android.hardware.health-service.qti_recovery"' in bp
    assert '"android.hardware.health@2.1-impl-qti"' not in bp
    assert '"android.hardware.health-service.qti.xml"' in bp

    main_cpp = (ROOT / "aidl/main.cpp").read_text()
    standard = main_cpp.index("::android::hardware::health::InitHealthdConfig(config.get());")
    vendor = main_cpp.index("qti_healthd_board_init(config.get());", standard)
    binder = main_cpp.index("ndk::SharedRefBase::make<Health>", vendor)
    assert standard < vendor < binder
    assert "ChargerModeMain" in main_cpp
    assert "HalHealthLoop" in main_cpp

    packages = (ROOT / "health-vendor-product.mk").read_text()
    active = [
        line.strip().split("+=", 1)[1].strip()
        for line in packages.splitlines()
        if re.match(r"^\s*PRODUCT_PACKAGES\s*\+=", line)
    ]
    assert active == [
        "android.hardware.health-service.qti",
        "android.hardware.health-service.qti_recovery",
        "charger_res_images_vendor",
    ], f"unexpected or legacy product packages: {active}"
    regular_rc = (ROOT / "aidl/android.hardware.health-service.qti.rc").read_text()
    recovery_rc = (ROOT / "aidl/android.hardware.health-service.qti_recovery.rc").read_text()
    assert "service vendor.health-default " in regular_rc
    assert "service vendor.charger " in regular_rc
    assert "class charger" in regular_rc
    assert "service vendor.health-recovery " in recovery_rc
    assert "hal_health_default" in recovery_rc

    print("PASS: AOSP17 Health AIDL V5 VINTF declaration")
    print("PASS: QTI AIDL normal/recovery product boundary, no legacy HIDL selected")
    print("PASS: AOSP health configuration initialized before Qualcomm override")
    print("SOURCE ONLY: Soong, vendor ABI, init/SELinux, charging and device boot untested")


if __name__ == "__main__":
    main()
