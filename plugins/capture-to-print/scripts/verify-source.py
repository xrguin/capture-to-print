"""Verify package file integrity; not a signature or a physical CAD assessment."""
from pathlib import Path
import hashlib
import json
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
manifest = json.loads((root/'PACKAGE_MANIFEST.json').read_text())
seen = set()
for row in manifest['files']:
    name = row['path']
    if name in seen:
        raise ValueError('Duplicate entry: '+name)
    seen.add(name)
    path = (root/name).resolve()
    path.relative_to(root)
    content = path.read_bytes()
    if len(content) != row['bytes'] or hashlib.sha256(content).hexdigest() != row['sha256']:
        raise ValueError('Missing or changed file: '+name)
print(json.dumps({'verified_files': len(seen), 'version': manifest['version'],
                  'scope': 'Listed file integrity, not independent validation or authenticity'}))
