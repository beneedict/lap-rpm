#!/bin/sh
# Startumbruch für Lap (RPM-Installation).
#
# Arbeitsumgehung für WebKitGTK 2.54.x: Der in 2.54 neue Skia-Compositor
# (WebCore::SkiaCompositingLayer) lässt den WebKit-Webprozess unbegrenzt
# wachsen, sobald die Oberfläche Elemente mit backdrop-filter enthält.
# Ursache ist WebKit-Bug 327701: paintBackdrop() repaintet den
# Backdrop-Teilbaum für jeden Backdrop-Layer erneut, der k-te Layer kostet
# also 2^(k-1) Teilbaum-Zeichenvorgänge. Messung auf Fedora 44 mit
# webkit2gtk4.1-2.54.1-1.fc44 und Lap 0.3.3:
#   ohne Schalter   WebKit-Webprozess 4,9 GiB nach 35 s, danach OOM
#   mit Schalter    flach bei etwa 0,34 GiB über 150 s
#
# WEBKIT_USE_SKIA_FOR_COMPOSITION=0 schaltet auf den alten
# TextureMapper-Compositor zurück: beschleunigtes Compositing bleibt aktiv.
# Alternative, falls es damit Darstellungsprobleme gibt:
#   WEBKIT_DISABLE_COMPOSITING_MODE=1  (Compositing komplett aus)
#
# Nicht mehr nötig, sobald Fedora webkit2gtk4.1 >= 2.54.2 liefert; darin sind
# die Fixes 324100@main und die 2.54-Rückportierung 317695.470@webkitglib/2.54
# enthalten, außerdem 317695.397@webkitglib/2.54 (Linux-Speicherverbrauch
# wurde immer als 0 gelesen).
#
# Ein schon gesetzter Wert wird nicht überschrieben.

if [ -z "${WEBKIT_USE_SKIA_FOR_COMPOSITION:-}" ]; then
    WEBKIT_USE_SKIA_FOR_COMPOSITION=0
    export WEBKIT_USE_SKIA_FOR_COMPOSITION
fi

exec /usr/libexec/lap-bin "$@"
