#!/usr/bin/env python3
"""Export local HA build inputs; never fetch or package a govee binary."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

# Pinned expected HEAD for the export: the review-fix commit on
# security/http-opt-in (SEC-01/02 + WB-17 warn-log + expert-review fixes).
# The worktree bundles the committed history plus the uncommitted
# lint cleanup and packaging changes.
BASELINE = "16ebe551ed01c357ef31601e10f456a0c11379fa"


def collect_tree(root, relative, output, prefix=""):
    path = root / relative
    if path.is_symlink():
        raise ValueError(f"Symlink input refused: {relative}")
    if path.is_dir():
        for child in sorted(path.iterdir()):
            collect_tree(root, child.relative_to(root), output, prefix)
    elif path.is_file():
        name = prefix + relative.as_posix()
        if any(c in name for c in "\n\r\\"):
            raise ValueError(f"Unsupported filename: {relative!r}")
        output[name] = path.read_bytes()
    else:
        raise ValueError(f"Missing build input: {relative}")


def prepare(source, destination):
    if destination.exists():
        raise ValueError("Destination exists; use a new directory (no implicit overwrite)")
    if destination.resolve().is_relative_to(source.resolve()):
        raise ValueError("Destination must be outside the source checkout")
    head = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != BASELINE:
        raise ValueError(f"Expected export pin {BASELINE}; found {head}")
    files = {}
    for name in ("Cargo.toml", "Cargo.lock", "build.rs", "src", "assets", "AmazonRootCA1.pem"):
        collect_tree(source, Path(name), files, "local-source/")
    for name in ("Dockerfile", "config.yaml", "build.yaml", "run.sh", "README.md", "DOCS.md", "CHANGELOG.md", "translations"):
        collect_tree(source / "addon", Path(name), files)
    files["PREPARE-SCRIPT.py"] = Path(__file__).read_bytes()
    config = files["config.yaml"].decode()
    dockerfile = files["Dockerfile"].decode()
    if re.search(r"^image\s*:", config, re.MULTILINE):
        raise ValueError("Registry image configuration refused: local HA build required")
    if "ghcr.io/wez/govee2mqtt" in dockerfile or ":latest" in dockerfile:
        raise ValueError("Upstream binary image or mutable latest reference refused")
    input_hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    content_id = hashlib.sha256(json.dumps(input_hashes, sort_keys=True).encode()).hexdigest()
    version = "0.3.0-local-" + content_id[:12]
    config, replacements = re.subn(r'^version:.*$', f'version: "{version}"', config, flags=re.MULTILINE)
    if replacements != 1:
        raise ValueError("Expected exactly one app version")
    files["config.yaml"] = config.encode()
    files["SOURCE_TAG"] = (version + "\n").encode()
    files["SOURCE.json"] = (json.dumps({
        "spec": "0.3", "baseline": head, "content_id": content_id,
        "version": version, "security_acceptance": "pending",
        "input_sha256": input_hashes,
        "architectures": {"amd64": "linux/amd64", "aarch64": "linux/arm64"},
    }, indent=2, sort_keys=True) + "\n").encode()
    # Deny accidental later-added .env, .git, target or host binary inputs.
    directories = sorted({str(parent) + "/" for name in files
                          for parent in Path(name).parents if str(parent) != "."})
    files[".dockerignore"] = ("**\n" + "\n".join("!" + name for name in directories)
                               + "\n" + "\n".join("!" + name for name in sorted(files))
                               + "\n!.dockerignore\n!SHA256SUMS\n").encode()
    files["SHA256SUMS"] = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(files.items())
    ).encode()
    destination.mkdir(parents=True)
    for name, data in sorted(files.items()):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o755 if name == "run.sh" else 0o644)
    return version


def archive_package(package, archive):
    # Stable order, ownership, mode and timestamps, including gzip header.
    with archive.open("xb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w") as tar:
                for path in sorted(package.rglob("*")):
                    if path.is_file():
                        data = path.read_bytes()
                        info = tarfile.TarInfo("govee2mqtt_security_local/" + path.relative_to(package).as_posix())
                        info.size = len(data)
                        info.mode = 0o755 if path.name == "run.sh" else 0o644
                        tar.addfile(info, io.BytesIO(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    if args.archive and args.archive.exists():
        parser.error("Archive exists; no overwrite")
    try:
        version = prepare(Path(__file__).resolve().parents[1], args.output)
        if args.archive:
            archive_package(args.output, args.archive)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Preparation failed: {exc}\n")
    print(f"Prepared {args.output}: {version}; security acceptance PENDING")


if __name__ == "__main__":
    main()
