#!/usr/bin/env python3
"""
AirCard-iOS CLI Pairing Injector
Cross-platform CLI tool to inject device pairing records into AirCard-iOS IPA.

Compatible with macOS, Linux, and Windows.
Automatically finds connected device pairing files or accepts a manual path.
"""

import os
import sys
import shutil
import zipfile
import plistlib
import argparse
from pathlib import Path
from typing import Optional, List

LOCKDOWN_PATHS = {
    "darwin": [Path("/var/db/lockdown")],
    "win32": [
        Path(os.environ.get("ProgramData", "C:\\ProgramData")) / "Apple" / "Lockdown",
        Path(os.environ.get("CommonProgramFiles", "C:\\Program Files\\Common Files")) / "Apple" / "Mobile Device Support" / "Lockdown"
    ],
    "linux": [Path("/var/lib/lockdown")]
}


def find_system_lockdown_files() -> List[Path]:
    """Search for system lockdown pairing files in default OS directories."""
    found: List[Path] = []
    platform = sys.platform
    paths_to_check = LOCKDOWN_PATHS.get(platform, [])

    for base_dir in paths_to_check:
        if base_dir.exists() and base_dir.is_dir():
            try:
                for entry in base_dir.iterdir():
                    if entry.is_file() and entry.suffix.lower() in [".plist", ".mobiledevicepairing"]:
                        if entry.name.lower() not in ["systemconfiguration.plist", "root.plist"]:
                            found.append(entry)
            except PermissionError:
                pass
    return sorted(found, key=lambda p: p.stat().st_mtime, reverse=True)


def validate_pairing_plist(path: Path) -> bool:
    """Validate structure of pairing file (Lockdown or RemotePairing)."""
    try:
        with open(path, "rb") as f:
            data = plistlib.load(f)
        if not isinstance(data, dict):
            return False
        is_lockdown = any(k in data for k in ("HostPrivateKey", "DeviceCertificate", "RootCertificate"))
        is_rppairing = any(k in data for k in ("e_private_key", "alt_irk", "identifier"))
        return is_lockdown or is_rppairing
    except Exception:
        return False


def find_default_ipa() -> Optional[Path]:
    """Find default IPA in current directory or build folder."""
    candidates = list(Path(".").glob("*.ipa")) + list(Path("build").glob("*.ipa"))
    filtered = [p for p in candidates if "injected" not in p.name.lower() and "personalized" not in p.name.lower()]
    if filtered:
        return filtered[0]
    return candidates[0] if candidates else None


def inject_pairing_into_ipa(ipa_path: Path, pairing_path: Path, output_path: Path) -> None:
    """Extract IPA, embed pairing plist files into Payload/*.app/, and repackage."""
    if not ipa_path.exists():
        raise FileNotFoundError(f"Source IPA not found: {ipa_path}")
    if not pairing_path.exists():
        raise FileNotFoundError(f"Pairing file not found: {pairing_path}")

    print(f"[*] Source IPA: {ipa_path}")
    print(f"[*] Pairing file: {pairing_path}")

    with open(pairing_path, "rb") as f:
        try:
            plist_dict = plistlib.load(f)
            # If lockdown plist lacks alt_irk, remove stale private_key to prevent timeout
            if isinstance(plist_dict, dict):
                if any(k in plist_dict for k in ("HostPrivateKey", "DeviceCertificate")) and "alt_irk" not in plist_dict:
                    plist_dict.pop("identifier", None)
                    plist_dict.pop("private_key", None)
                    plist_dict.pop("public_key", None)
            pairing_data = plistlib.dumps(plist_dict)
        except Exception:
            f.seek(0)
            pairing_data = f.read()

    temp_dir = Path("temp_inject_workspace")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        print("[*] Unpacking IPA archive...")
        with zipfile.ZipFile(ipa_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        payload_dir = temp_dir / "Payload"
        if not payload_dir.exists():
            raise RuntimeError("Missing Payload/ folder inside IPA")

        app_dirs = [d for d in payload_dir.iterdir() if d.is_dir() and d.suffix == ".app"]
        if not app_dirs:
            raise RuntimeError("No .app bundle found inside Payload/")

        app_dir = app_dirs[0]
        print(f"[*] Target app bundle: {app_dir.name}")

        target_names = [
            "aircard_pairing.plist",
            "airlift_pairing.plist",
            "pairing.plist",
            pairing_path.name
        ]

        for target_name in set(target_names):
            dest_file = app_dir / target_name
            with open(dest_file, "wb") as f:
                f.write(pairing_data)
            print(f"    [+] Embedded: {app_dir.name}/{target_name}")

        print(f"[*] Packaging personalized IPA: {output_path}...")
        if output_path.exists():
            output_path.unlink()

        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_out:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_full = Path(root) / file
                    arc_name = file_full.relative_to(temp_dir)
                    zinfo = zipfile.ZipInfo.from_file(file_full, arcname=str(arc_name))
                    st = file_full.stat()
                    zinfo.external_attr = (st.st_mode & 0xFFFF) << 16
                    with open(file_full, "rb") as f_in:
                        zip_out.writestr(zinfo, f_in.read())

        print(f"[OK] Done! Ready-to-install IPA created at: {output_path}")
        print(f"     Size: {output_path.stat().st_size / (1024 * 1024):.2f} MB")
        print("     Install via AltStore, SideStore, TrollStore, Feather, or iLoader.")

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def main():
    parser = argparse.ArgumentParser(
        description="AirCard-iOS Pairing Injector — embed pairing records into IPA"
    )
    parser.add_argument("-i", "--ipa", type=Path, help="Path to input AirCard-iOS.ipa")
    parser.add_argument("-p", "--pairing", type=Path, help="Path to pairing file (.plist / .mobiledevicepairing)")
    parser.add_argument("-o", "--output", type=Path, help="Path to output personalized IPA")

    args = parser.parse_args()

    ipa_path = args.ipa
    if not ipa_path:
        ipa_path = find_default_ipa()
        if not ipa_path:
            sys.exit("[-] Error: IPA not specified and not found in current directory. Use -i <path_to_ipa>")

    pairing_path = args.pairing
    if not pairing_path:
        detected = find_system_lockdown_files()
        if detected:
            print("[*] Found system pairing records:")
            for idx, p in enumerate(detected[:5], 1):
                print(f"    [{idx}] {p}")
            choice = input(f"Select file number [1-{min(5, len(detected))}] or type path manually: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= min(5, len(detected)):
                pairing_path = detected[int(choice) - 1]
            elif choice:
                pairing_path = Path(choice)
            else:
                pairing_path = detected[0]
        else:
            choice = input("Enter path to your pairing file (.plist): ").strip().strip("'\"")
            if not choice:
                sys.exit("[-] Error: No pairing file specified.")
            pairing_path = Path(choice)

    if not validate_pairing_plist(pairing_path):
        print(f"[!] Warning: {pairing_path} does not match standard lockdown/RPPairing format.")
        confirm = input("Continue injection anyway? [y/N]: ").strip().lower()
        if confirm != "y":
            sys.exit("[-] Aborted by user.")

    output_path = args.output
    if not output_path:
        stem = ipa_path.stem
        output_path = ipa_path.parent / f"{stem}-Personalized.ipa"

    inject_pairing_into_ipa(ipa_path, pairing_path, output_path)


if __name__ == "__main__":
    main()
