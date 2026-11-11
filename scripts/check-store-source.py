#!/usr/bin/env python3
"""Check authoritative add-on inputs; --write refreshes only generated metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import re

# Historical origin of the reconciled fork, not the current source revision.
BASELINE = '9b10da79bc1f184a181b3d008f68d6996d9a807a'
INPUTS = ('Dockerfile', 'config.yaml', 'build.yaml', 'run.sh', 'README.md',
          'DOCS.md', 'CHANGELOG.md', 'LICENSE.md', 'translations',
          'local-source/Cargo.toml', 'local-source/Cargo.lock',
          'local-source/build.rs', 'local-source/AmazonRootCA1.pem',
          'local-source/src', 'local-source/assets', 'local-source/vendor',
          'local-source/test-data')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def generated_files(store):
    files = {}

    def collect(path):
        name = path.relative_to(store).as_posix()
        if path.is_symlink() or any(c in name for c in '\n\r\\!*?[]'):
            raise ValueError(f'Unsafe build input: {name}')
        if any(p.startswith('.env') or p in ('.git', 'target', '__pycache__')
               for p in path.relative_to(store).parts):
            raise ValueError(f'Private or generated build input refused: {name}')
        if path.is_dir():
            for child in sorted(path.iterdir()):
                collect(child)
        else:
            files[name] = path.read_bytes()

    for name in INPUTS:
        collect(store / name)
    versions = re.findall(r'^version: "([^"\n]+)"$', files['config.yaml'].decode(), re.M)
    if len(versions) != 1:
        raise ValueError('Expected one quoted config.yaml version')
    version = versions[0]
    hashes = {name: digest(data) for name, data in sorted(files.items())}
    generated = {
        'SOURCE_TAG': (version + '\n').encode(),
        'SOURCE.json': (json.dumps({
            'spec': '1', 'baseline': BASELINE, 'source_layout': 'in-context',
            'content_id': digest(json.dumps(hashes, sort_keys=True).encode()),
            'version': version, 'security_acceptance': 'pending',
            'architectures': {'amd64': 'linux/amd64', 'aarch64': 'linux/arm64'},
            'input_sha256': hashes,
        }, indent=2, sort_keys=True) + '\n').encode(),
    }
    # Exact allowlist: host credentials, targets and unrelated files never enter Docker.
    names = sorted(set(files) | set(generated) | {'.dockerignore', 'SHA256SUMS'})
    directories = sorted({str(p) + '/' for n in names for p in Path(n).parents
                          if str(p) != '.'})
    generated['.dockerignore'] = ('**\n' + ''.join('!' + n + '\n' for n in directories + names)).encode()
    generated['SHA256SUMS'] = ''.join(
        f'{digest(data)}  {name}\n' for name, data in sorted((files | generated).items())
    ).encode()
    return generated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store', type=Path,
                        default=Path(__file__).resolve().parents[1] / 'govee2mqtt_security_local')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    try:
        expected = generated_files(args.store)
        stale = []
        for name, data in expected.items():
            path = args.store / name
            if path.is_symlink():
                raise ValueError(f'Symlink metadata refused: {name}')
            if args.write:
                path.write_bytes(data)
            elif not path.exists() or path.read_bytes() != data:
                stale.append(name)
        if stale:
            raise ValueError('stale metadata: ' + ', '.join(stale) + '; run scripts/check-store-source.py --write')
    except (OSError, ValueError) as exc:
        print(f'FAIL: {exc}')
        return 1
    print('store source ok' + ('; metadata refreshed' if args.write else ''))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
