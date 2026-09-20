# AirCard-iOS

<p align="center">
  <img src="ios-app/Assets.xcassets/AppIcon.appiconset/AppIcon.png" width="128" height="128" alt="AirCard-iOS Icon" style="border-radius: 28px; box-shadow: 0 8px 24px rgba(0,0,0,0.18);" />
</p>

<p align="center">
  Apple Wallet card skins, lock screen passcode themes, and PosterBoard wallpapers directly on iOS 26 – 27+.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-iOS%2026%20--%2027%2B-blue?style=flat-square&logo=apple" alt="Platform" />
  <img src="https://img.shields.io/badge/Swift-5.0-orange?style=flat-square&logo=swift" alt="Swift" />
  <img src="https://img.shields.io/badge/Rust-FFI%20Core-red?style=flat-square&logo=rust" alt="Rust" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
  <a href="https://www.paypal.com/donate/?hosted_button_id=98QRTC2HFRA4Y"><img src="https://img.shields.io/badge/Donate-PayPal-00457C?style=flat-square&logo=paypal" alt="Donate with PayPal" /></a>
</p>

## Overview

AirCard-iOS customizes Apple Wallet card artwork, lock screen passcode dialers, and lock screen wallpapers on device without a jailbreak.

The app communicates with internal system services over a local loopback tunnel (`10.7.0.1` or `127.0.0.1`) provided by LocalDevVPN. File operations are handled by `AirliftFFI`, a Rust library that interfaces with the AirTraffic service.

### 📱 iOS Version Support (iOS 26 – 27+)

AirCard-iOS supports both **iOS 26** and **iOS 27+** (as well as iOS 17+ via RemotePairing):

| Feature / Behavior | iOS 27+ | iOS 26 |
|---|---|---|
| **On-device Developer Mode Pairing** | ✅ Available in *Settings › Privacy & Security › Developer Mode* | ❌ Removed by Apple from Settings |
| **Local lockdown loopback (`:62078`)** | ✅ Supported via LocalDevVPN | ❌ Blocked by Apple (`Broken pipe` / socket rejection) |
| **RemotePairing RSD Tunnel (`:49152`)** | ✅ Supported | ✅ **Primary method** (requires pairing record with `alt_irk`) |
| **AirCard Injector / `idevice_pair`** | Optional | **Recommended** (1-click pairing file generation & IPA injection) |

> **How iOS 26 support works**: Starting in iOS 26, Apple removed the built-in Developer Mode pairing menu from Settings and blocked unauthenticated loopback access to `lockdownd:62078`. AirCard-iOS resolves this by establishing an RSD (Remote Service Discovery) tunnel over port `49152`. Pairing once with **[idevice_pair](https://github.com/jkcoxson/idevice_pair)** generates a complete RemotePairing record containing the required 16-byte `alt_irk` key, allowing the app to authenticate and operate seamlessly on iOS 26.

## Features

### Apple Wallet card skins
- Writes custom card artwork to Passbook caches (`cardBackgroundCombined@3x.png`, `@2x.png`, and `cardBackgroundCombined.pdf` for transit cards like Suica).
- Flushes front-face and thumbnail caches so new artwork appears immediately when Wallet opens.
- Detects card identifiers in real time when you bring up Apple Pay.
- Apply artwork to individual cards or batch-flash every detected card.

### Passcode dialer themes
- Live dialer preview with touch panning and zoom framing.
- Full poster layout across all ten buttons, or individual circular button cutouts.
- Targets system dialer caches (`TelephonyUI-10`).
- Localized number subtext options, including Ukrainian and Russian Cyrillic layouts.
- Import and export themes as `.passthm` files.

### PosterBoard wallpapers (.tendies)
- Import and unpack `.tendies` wallpaper archives directly from the Files app.
- Auto-detects PosterBoard wallpaper containers and active descriptor UUIDs.
- Injects wallpaper configurations and assets into PosterBoard storage.
- Automatically triggers a NeoSpring respring after flashing to apply wallpapers without rebooting your iPhone.

### On-device pairing
- Advertises locally over Bonjour so the phone can pair with itself via Settings > Privacy & Security > Developer Mode > Pair with AirCard-iOS (on supported versions).
- Reads and syncs pairing records automatically into `aircard_pairing.plist`.
- Once paired, no computer or external connection is needed.
- **For iOS versions without on-device Developer Mode pairing (iOS 26+)**: Devices can pair once via [idevice_pair](https://github.com/jkcoxson/idevice_pair) to generate a RemotePairing record with `alt_irk` (port `49152`), or inject it directly into the IPA using **AirCard Injector** (`tools/mac-injector`).

## Prerequisites

1. **iOS 26 – 27+**: Compatible with iOS 27+, and iOS 26 (as well as iOS 17+) via RemotePairing (RSD).
2. **LocalDevVPN**: Running in loopback mode (`10.7.0.1` or `127.0.0.1`) so local connections can reach internal device services.
3. **Pairing credentials**:
   - **iOS 27+**: Pair directly in Settings > Privacy & Security > Developer Mode > Pair with AirCard-iOS.
   - **iOS 26**: Generate a RemotePairing record using `idevice_pair` (or AirCard Injector) and embed/import it as `pairingFile.plist` / `aircard_pairing.plist`.

## Installation

Install `AirCard-iOS.ipa` using your preferred sideloading method:

- SideStore or AltStore
- TrollStore
- LiveContainer
- Xcode or iOS App Signer

### AirCard Injector (Optional Helper Tool)

If your iOS version lacks on-device Developer Mode pairing or has locked-down `lockdownd` loopback access, you can use the included helper tools in `tools/`:

- **macOS App (`tools/mac-injector`)**: A native SwiftUI app packaged with embedded `idevice_pair` to generate the RemotePairing file and inject it into the IPA in 1 click. Run `./tools/mac-injector/build_app.sh` to build `AirCardInjector.dmg`.
- **CLI Tool (`tools/cli-injector`)**: Cross-platform Python script (`inject_pairing.py`) for Linux, Windows, and macOS.

## Building from source

### Requirements
- macOS 14.0 or newer with Xcode 16 or newer
- XcodeGen (`brew install xcodegen`)
- Rust toolchain (only needed if rebuilding `rust-core`)

### Build the IPA
```bash
git clone https://github.com/mak5er/AirCard-iOS.git
cd AirCard-iOS
./build-ipa.sh
```

The completed package is written to `build/AirCard-iOS.ipa`.

### Rebuilding the Rust framework
To compile changes in `rust-core`:
```bash
./build-ios.sh
```

## Repository structure

```
AirCard-iOS/
├── ios-app/                   # SwiftUI application
│   ├── AirCardApp.swift       # App entry point and lifecycle
│   ├── AppViewModel.swift     # State management and exploit orchestration
│   ├── ContentView.swift      # Main UI views
│   ├── TendiesView.swift      # PosterBoard wallpaper view
│   ├── TendiesEngine.swift    # Tendies extraction and injection logic
│   ├── RespringHelper.swift   # NeoSpring WebKit respring implementation
│   ├── Models.swift           # Image slicing, theme layout, archive packing
│   ├── PairingController.swift# Bonjour host and pairing sync
│   ├── NetworkStatus.swift    # VPN loopback detection
│   ├── Utilities.swift        # Background keep-alive and helper functions
│   ├── GrappaHelper.[h,m]     # ATC protocol helpers
│   ├── Info.plist             # Bundle configuration
│   └── Assets.xcassets/       # App icons and image sets
├── tools/
│   ├── mac-injector/          # Native macOS SwiftUI pairing injector app & DMG packager
│   └── cli-injector/          # Cross-platform CLI injector (inject_pairing.py)
├── AirliftFFI.xcframework/    # Compiled arm64 Rust static library and headers
├── rust-core/                 # Rust core source code
├── project.yml                # XcodeGen project definition
├── build-ipa.sh               # IPA build script
├── build-ios.sh               # Rust framework build script
├── LICENSE                    # MIT License
└── README.md                  # Project documentation
```

## Credits

- **[@mak5er](https://github.com/mak5er)**: Lead developer, UI, passcode theming, Tendies engine, on-device pairing.
- **[@merybist](https://github.com/merybist)**: Initial base port, iOS 26 RemotePairing research, and AirCard Injector macOS tooling.
- **[@jkcoxson](https://github.com/jkcoxson)**: Creator of [idevice_pair](https://github.com/jkcoxson/idevice_pair) and the `idevice` Rust ecosystem for RemotePairing support.
- **[AirLift](https://github.com/0xjohnnydev/airlift)** by **[0xjohnny (@0xjohnnydev)](https://github.com/0xjohnnydev)**: AirTraffic and ATAirlock sandbox escape research underlying `AirliftFFI`.
- **[NeoSpring](https://github.com/rooootdev/neospring)**: Swift implementation by **[@skadz108](https://github.com/skadz108)** and **[@rooootdev](https://github.com/rooootdev)**, and **[@neonmodder123](https://github.com/neonmodder123)** for the WebKit GPU process respring technique.
- Built upon concepts from the **AirCard** project.

## Support

If you want to support AirCard-iOS development:

- **PayPal**: [Donate via PayPal](https://www.paypal.com/donate/?hosted_button_id=98QRTC2HFRA4Y)
- **TON**: `UQBm9KPhtMw-XVVjirUoa09wzrlyWsbeZhKfefl1Uw-qNZ-r`
- **USDT (TRC20)**: `TDkDMCyjYxgvkWUnQiF5Erk2RyPQMT6G1n`
- **USDT / BNB (BEP20)**: `0x0954dc491c502849d04956ef74634aa5931a08e8`

## License

MIT License. See [LICENSE](LICENSE) for details.
