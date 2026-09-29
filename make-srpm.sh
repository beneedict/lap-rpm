#!/usr/bin/env bash
# Erzeugt das Quellpaket (SRPM) für Lap.
# Aufruf: ./make-srpm.sh <Version>   Beispiel: ./make-srpm.sh 0.3.2
# Das GitHub-Archiv eines Tags enthält keine Submodule. Deshalb klont das
# Skript den Tag mit allen Submodulen und packt ihn selbst.
set -euo pipefail

VERSION="${1:?Aufruf: $0 <Version>}"
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/out"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$OUT"

git clone --quiet --depth 1 --recurse-submodules --shallow-submodules \
    --branch "v$VERSION" https://github.com/julyx10/lap.git "$WORK/lap-$VERSION"
# libde265 ist ein HEVC-Decoder (Patente). Fedora und COPR dürfen ihn nicht
# verteilen, auch nicht als Quellcode. Das RPM nutzt die System-libheif.
# Deshalb braucht der Bau auch die eigene libheif nicht.
rm -rf "$WORK/lap-$VERSION/src-tauri/third_party/libde265" \
       "$WORK/lap-$VERSION/src-tauri/third_party/libheif"
tar -C "$WORK" --exclude=.git -czf "$OUT/lap-$VERSION.tar.gz" "lap-$VERSION"

# Bei neuer Version: Version setzen, Release auf 1, %changelog-Eintrag.
SPEC="$DIR/lap.spec"
PACKAGER="Benedikt Nimmervoll <nimmervoll.benedikt+copr@gmail.com>"
CURRENT="$(sed -n 's/^Version:[[:space:]]*//p' "$SPEC")"
if [[ "$CURRENT" != "$VERSION" ]]; then
    rpmdev-bumpspec -n "$VERSION" -c "Update auf $VERSION" -u "$PACKAGER" "$SPEC"
fi

cp "$SPEC" "$DIR/lap.desktop" "$DIR/lap-face-models" "$DIR/lap-system-libheif.patch" "$OUT/"
rpmbuild -bs \
    --define "_sourcedir $OUT" \
    --define "_srcrpmdir $OUT" \
    "$OUT/lap.spec"

ls -1 "$OUT"/*.src.rpm
