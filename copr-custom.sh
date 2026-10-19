#!/bin/bash
# COPR-Quellmethode "Custom" für Lap. COPR führt das Skript mit Netzwerk aus.
# Es holt die Paketdateien aus https://github.com/beneedict/lap-rpm und den
# Quellcode von Lap. Ergebnis im aktuellen Ordner: lap.spec und Quellen.
# Version: aus hook_payload ({"version": "x.y.z"} oder GitHub-Release-Event),
# sonst das neueste Release von julyx10/lap.
set -euo pipefail

VERSION=""
if [[ -s hook_payload ]]; then
    VERSION="$(jq -r '.version // .release.tag_name // empty' hook_payload 2>/dev/null || true)"
fi
if [[ -z "$VERSION" ]]; then
    VERSION="$(curl -fsSL https://api.github.com/repos/julyx10/lap/releases/latest | jq -r .tag_name)"
fi
VERSION="${VERSION#v}"
if [[ ! "$VERSION" =~ ^[0-9]+(\.[0-9]+)*$ ]]; then
    echo "Ungültige Version: '$VERSION'" >&2
    exit 1
fi
echo "Lap-Version: $VERSION"

git clone --quiet --depth 1 https://github.com/beneedict/lap-rpm.git pkg
cp pkg/lap.spec pkg/lap.desktop pkg/lap-wrapper.sh pkg/lap-face-models pkg/lap-system-libheif.patch .
rm -rf pkg

# libde265 (HEVC, Patente) und libheif nicht verteilen. Das RPM nutzt die System-libheif.
git clone --quiet --depth 1 --recurse-submodules --shallow-submodules \
    --branch "v$VERSION" https://github.com/julyx10/lap.git "lap-$VERSION"
rm -rf "lap-$VERSION/src-tauri/third_party/libde265" \
       "lap-$VERSION/src-tauri/third_party/libheif"
tar --exclude=.git -czf "lap-$VERSION.tar.gz" "lap-$VERSION"
rm -rf "lap-$VERSION"

CURRENT="$(sed -n 's/^Version:[[:space:]]*//p' lap.spec)"
if [[ "$CURRENT" != "$VERSION" ]]; then
    rpmdev-bumpspec -n "$VERSION" -c "Update auf $VERSION" \
        -u "Benedikt Nimmervoll <nimmervoll.benedikt+copr@gmail.com>" lap.spec
fi
ls -la
