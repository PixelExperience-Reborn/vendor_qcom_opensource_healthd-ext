# PixelExperience-Reborn Android 17 — Qualcomm Health AIDL V5 source port (mondrian)

**Review date:** 2026-11-07. **Scope:** independent PE-Reborn AOSP17 base and a future native POCO F5 Pro / Redmi K60 (`mondrian`, SM8475) product. **Status:** strictly isolated AIDL source candidate. Not in any active AOSP17 manifest or product. No Soong build, charger, recovery or on-device test.

## Source authority and selection

1. **Primary API/implementation:** verified PE-Reborn `hardware_interfaces` AOSP17 fork [`port/a17-hardware-interfaces-pe-20261103`](https://github.com/PixelExperience-Reborn/hardware_interfaces/tree/port/a17-hardware-interfaces-pe-20261103), commit `735e364cbdd00b0d6e4dc33ea0866dbb6d971a11`. This `health/aidl/default/Android.bp` defines `libhealth_aidl_impl_user` against **`android.hardware.health-V5-ndk`**, and its own `android.hardware.health-service.example.xml` advertises **Health AIDL V5**. Official [AOSP Health AIDL HAL documentation](https://github.com/PixelExperience-Reborn/hardware_interfaces/blob/port/a17-hardware-interfaces-pe-20261103/health/aidl/README.md) requires base `InitHealthdConfig()` before board-specific changes.
2. **Older Qualcomm vendor source:** PE `vendor_qcom_opensource_healthd-ext` `seventeen` commit `398ea4b554fffbed4a59294b51085b7eba8b5f5d` (2023-08-03), Qualcomm LA.VENDOR.13.2.0. Source already supplies `android.hardware.health-service.qti` with `libhealth_aidl_impl_user` but still declares **VINTF Health AIDL V1**, and applies Qualcomm board settings before base AOSP initialization. Root `Android.bp` also declares a **legacy HIDL 2.1 implementation**, not automatically chosen by the AIDL `health-vendor-product.mk`.
3. **Independent comparison only:** LineageOS 24.0 Qualcomm `healthd-ext` commit `9bdd090e6b5797d339e96b060c03412f36993554` (2026-10-12) bumps the HAL VINTF declaration to V5 and includes other SoC power-supply selection logic. This corroborates the generation mismatch but is **not the PE-Reborn source base**; the other SoC IDs and settings have not been copied.
4. **Hardware evidence only:** LF52406 `sm8450-common/common.mk` already lists `android.hardware.health-service.qti` and its recovery variant; it also installs a separate `vendor.lineage.health-service.default` that is **Lineage-specific and must not be added to PE-Reborn**. Real stock/PE vendor interfaces, charging files and battery paths must be checked independently.

## Isolated edits in this branch

| File | Reviewed change | Reason |
| --- | --- | --- |
| `aidl/android.hardware.health-service.qti.xml` | AIDL Health version **1 → 5**, still `IHealth/default` | Match the actual AOSP17 `libhealth_aidl_impl_user` / `android.hardware.health-V5-ndk` service implementation. This is a VINTF source alignment, not an upgrade of the physical battery controller. |
| `aidl/main.cpp` | Call `InitHealthdConfig(config.get())` **before** `qti_healthd_board_init(config.get())` | Apply board-specific power-supply filtering after default settings, as AOSP17 documents. No SOC-specific paths, vendor properties or modem integrations were imported. |
| `tests/check_android17_health_aidl.py` | Validate AIDL V5, intended product packages, one standard/recovery service, initialization order and no legacy HIDL module in selected AIDL packages | Offline source-only gate, no false claim of compile or boot. |
| `.github/workflows/a17-health-aidl-source-check.yml` | Run the offline gate on branch changes and PRs | CI visibility for source invariants only. |

Unchanged: `health-vendor-product.mk` packages the normal and recovery QTI AIDL service plus `charger_res_images_vendor`; `aidl/Android.bp` retains the AOSP17-relevant `libhealth_aidl_impl_user` default, `libhealth_aidl_impl` and init rc entry points. The old HIDL source stays in historical inventory, but is **not declared as an active product dependency** by this product makefile.

## Mandatory checks before product adoption

- **Hardware/sysfs:** validate `/sys/class/power_supply/battery/capacity` and UCSI power-supply naming on the actual device and its vendor firmware. Review the QTI polling/retry loop for boot delays, errors and doze/recovery behavior; no speculative `ro.vendor.qti.soc_id` overrides.
- **Binary/Soong:** compile against the selected AOSP17 `health/aidl` and `system/core` code, verify all recovery and vendor static/shared dependencies, exported headers, required stubs and VNDK/LLNDK boundaries; inspect the resulting ELF dependencies rather than relying on `Android.bp` alone.
- **VINTF:** verify that exactly one `android.hardware.health IHealth/default` implementation is installed at frozen version 5 and that the relevant FCM matrix accepts it. Avoid duplicate AIDL/HIDL services, duplicate `charger` class service registration and conflicting vendor XML declarations.
- **Recovery/offline charging:** test `vendor.health-default`, `vendor.charger` and `vendor.health-recovery` init services; charger resource location under vendor, correct display/offline charging, safe shutdown/suspend, input and permissions.
- **SELinux/security:** check `charger_vendor`, `hal_health_default`, service manager permissions, power_supply sysfs labels, file access under enforcing mode. Never apply blanket permissive or broad allow rules.
- **Runtime:** inspect battery capacity/current/temperature, charging state, unplugged shutdown, notifications, charging while off, recovery battery reporting, battery drain and suspend, with logging and CTS/VTS where available.
- **Independent product only:** after PE-Reborn native device trees exist, own this HAL in the new tree and use compatible vendor blobs. Do not copy or install `vendor.lineage.health-service.default`.

**Decision:** advance the modern **AOSP17 Health AIDL V5** Qualcomm QTI service as a **nondefault candidate**; the current AOSP17 manifest and Xiaomi product integration remain unchanged. The stage is a reviewed source port, **not a completed device HAL migration**.
