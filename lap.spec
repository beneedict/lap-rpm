# Lap: Offline-Fotomanager (Tauri 2). Baut aus dem Quellcode.
# Der Bau braucht Netzwerk: Cargo, pnpm, ort (ONNX Runtime) und die KI-Modelle
# kommen aus dem Internet. In COPR: Projekt mit "--enable-net on" anlegen.
# Das Archiv erzeugt make-srpm.sh. Es enthält LibRaw und libjpeg-turbo, nicht libheif und libde265.

# Cargo-Profil setzt strip = true. Es gibt keine Debug-Informationen.
%global debug_package %{nil}

# Lap erwartet die FFmpeg-Dateien mit dem Rust-Target im Namen.
%ifarch x86_64
%global lap_triple x86_64-unknown-linux-gnu
%else
%global lap_triple aarch64-unknown-linux-gnu
%endif

Name:           lap
Version:        0.3.2
Release:        2%{?dist}
Summary:        Offline-first photo manager for large local libraries
License:        GPL-3.0-or-later
URL:            https://github.com/julyx10/lap
Source0:        %{name}-%{version}.tar.gz
Source1:        lap.desktop
# Die InsightFace-Modelle dürfen nicht weitergegeben werden.
# Dieses Skript lädt sie auf dem Zielrechner.
Source2:        lap-face-models
# Linkt gegen die System-libheif statt libheif und libde265 selbst zu bauen.
# HEVC (HEIC-Fotos) kommt dann über das Plugin aus libheif-freeworld (RPM Fusion).
# Nur für Lap 0.3.2 und älter. %%prep wendet ihn nur bei Bedarf an.
Patch0:         lap-system-libheif.patch

ExclusiveArch:  x86_64 aarch64

BuildRequires:  cargo >= 1.85
BuildRequires:  rust >= 1.85
BuildRequires:  nodejs >= 20
BuildRequires:  pnpm
BuildRequires:  cmake
BuildRequires:  nasm
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  clang
BuildRequires:  make
BuildRequires:  curl
BuildRequires:  pkgconf-pkg-config
BuildRequires:  desktop-file-utils
BuildRequires:  pkgconfig(webkit2gtk-4.1)
BuildRequires:  pkgconfig(javascriptcoregtk-4.1)
BuildRequires:  pkgconfig(libsoup-3.0)
BuildRequires:  pkgconfig(gtk+-3.0)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(ayatana-appindicator3-0.1)
BuildRequires:  pkgconfig(librsvg-2.0)
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(libheif) >= 1.17
BuildRequires:  libxdo-devel
BuildRequires:  oniguruma-devel

# Lap startet FFmpeg als externes Programm. Jedes Paket mit diesen Dateien
# erfüllt die Abhängigkeit: ffmpeg-free (Fedora) oder ffmpeg (RPM Fusion).
Requires:       /usr/bin/ffmpeg
Requires:       /usr/bin/ffprobe
Requires:       hicolor-icon-theme
# Für lap-face-models
Requires:       curl

%description
Lap is an offline-first photo manager for large local libraries. It indexes
folders in place, reads RAW and HEIF files, and offers local AI search and
face grouping without cloud uploads.

%prep
%autosetup -N -n %{name}-%{version}
# Lap-Versionen nach 0.3.2 enthalten LAP_SYSTEM_LIBHEIF selbst (PR #359).
# Der Patch ist nur für ältere Versionen nötig.
if ! grep -q LAP_SYSTEM_LIBHEIF src-tauri/build.rs; then
%patch -P 0 -p1
fi

%build
export CARGO_HOME="$PWD/.cargo-home"
export CARGO_PROFILE_RELEASE_STRIP=true
export NUM_JOBS=%{_smp_build_ncpus}
export LAP_SYSTEM_LIBHEIF=1

bash scripts/download_models.sh

# tauri-build verlangt Dateien unter resources/ffmpeg/. Das RPM nutzt das
# FFmpeg des Systems (Links im Install-Abschnitt). Leere Platzhalter genügen.
mkdir -p src-tauri/resources/ffmpeg
touch src-tauri/resources/ffmpeg/ffmpeg-%{lap_triple} \
      src-tauri/resources/ffmpeg/ffprobe-%{lap_triple}

pnpm --dir src-vite install --frozen-lockfile
pnpm --dir src-vite build

cd src-tauri
cargo build --release --locked -j %{_smp_build_ncpus}

%install
# Tauri 2 sucht Ressourcen auf Linux unter /usr/lib/<productName>.
install -Dpm 0755 src-tauri/target/release/Lap %{buildroot}%{_bindir}/lap

install -Dpm 0755 %{SOURCE2} %{buildroot}%{_bindir}/lap-face-models

# Nur die CLIP-Dateien (MIT). Die InsightFace-Dateien lädt lap-face-models.
install -d %{buildroot}%{_prefix}/lib/Lap/models
install -pm 0644 src-tauri/resources/models/{tokenizer.json,text_model.onnx,vision_model.onnx} \
    %{buildroot}%{_prefix}/lib/Lap/models/

install -d %{buildroot}%{_prefix}/lib/Lap/ffmpeg
ln -s %{_bindir}/ffmpeg  %{buildroot}%{_prefix}/lib/Lap/ffmpeg/ffmpeg-%{lap_triple}
ln -s %{_bindir}/ffprobe %{buildroot}%{_prefix}/lib/Lap/ffmpeg/ffprobe-%{lap_triple}

install -Dpm 0644 src-tauri/icons/icon.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/lap.png
desktop-file-install --dir=%{buildroot}%{_datadir}/applications %{SOURCE1}

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/lap.desktop

%files
%license LICENSE
%doc README.md PRIVACY.md
%{_bindir}/lap
%{_bindir}/lap-face-models
%{_prefix}/lib/Lap/
%ghost %{_prefix}/lib/Lap/models/det_500m.onnx
%ghost %{_prefix}/lib/Lap/models/w600k_mbf.onnx
%{_datadir}/applications/lap.desktop
%{_datadir}/icons/hicolor/512x512/apps/lap.png

%changelog
* Sun Sep 27 2026 Benedikt Nimmervoll <nimmervoll.benedikt+copr@gmail.com> - 0.3.2-2
- InsightFace-Modelle aus dem Paket entfernt (Lizenz)
- Neues Skript lap-face-models lädt sie auf dem Zielrechner
- System-libheif statt eigener libheif/libde265 (kein HEVC-Code im Paket)

* Thu Sep 24 2026 Benedikt Nimmervoll <nimmervoll.benedikt+copr@gmail.com> - 0.3.2-1
- Erstes Paket, Bau aus dem Quellcode
