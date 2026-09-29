# Lap als RPM (Fedora COPR)

Dieses Repository baut [Lap](https://github.com/julyx10/lap) als RPM aus dem Quellcode.
COPR baut das Paket und stellt es als `dnf`-Repository bereit:
https://copr.fedorainfracloud.org/coprs/beneedict/lap/

## Dateien

| Datei | Zweck |
|---|---|
| `lap.spec` | RPM-Spec. Der Bau lädt Crates, npm-Pakete, ONNX Runtime und KI-Modelle aus dem Internet. |
| `lap.desktop` | Menüeintrag |
| `lap-face-models` | Lädt die Gesichtsmodelle von InsightFace auf dem Zielrechner. Wird nach `/usr/bin/` installiert. |
| `make-srpm.sh` | Klont einen Tag mit allen Submodulen und erzeugt das SRPM in `out/`. |
| `copr-custom.sh` | Skript für die COPR-Quellmethode „Custom“. Erzeugt Spec und Quellen in COPR. |

## Voraussetzungen

1. Installiere die Werkzeuge: `sudo dnf install mock rpmdevtools rpmlint copr-cli`
2. Füge deinen Benutzer zur Gruppe `mock` hinzu: `sudo usermod -aG mock $USER`
3. Melde dich ab und wieder an.

## Lokal bauen und testen

1. Erzeuge das SRPM: `./make-srpm.sh 0.3.2`
2. Baue das RPM mit Netzwerk:
   `mock -r fedora-44-x86_64 --enable-network --rebuild out/lap-0.3.2-1.fc44.src.rpm`
3. Das RPM liegt danach in `/var/lib/mock/fedora-44-x86_64/result/`.
4. Prüfe das RPM: `rpmlint /var/lib/mock/fedora-44-x86_64/result/lap-0.3.2-1.fc44.x86_64.rpm`

## COPR einrichten (einmalig)

COPR-Projekte sind öffentlich. Das RPM enthält deshalb keine Dateien, deren
Lizenz die Weitergabe verbietet. Siehe Abschnitt „Gesichtserkennung“.

1. Lege ein Fedora-Konto an: https://accounts.fedoraproject.org
2. Melde dich an: https://copr.fedorainfracloud.org
3. Öffne https://copr.fedorainfracloud.org/api und kopiere den Inhalt nach `~/.config/copr`.
   Gib den Token an niemanden weiter.
4. Lege das Projekt mit Netzwerk beim Bau an:
   `copr-cli create lap --chroot fedora-44-x86_64 --enable-net on`

## Bauen in COPR

Das Paket `lap` nutzt die Quellmethode „Custom“. COPR führt `copr-custom.sh` aus:

1. Es liest die Version aus der Webhook-Nutzlast (`hook_payload`). Ohne Nutzlast nimmt es das neueste Release von Lap.
2. Es klont dieses Repository und holt Spec, Patch und die übrigen Dateien.
3. Es klont Lap mit den Submodulen und entfernt `libheif` und `libde265`.
4. Bei neuer Version setzt es `Version`, `Release: 1` und einen `%changelog`-Eintrag mit `rpmdev-bumpspec`.

Das Skript in COPR eintragen (nach jeder Änderung an `copr-custom.sh`):

```
copr-cli edit-package-custom lap --name lap --script copr-custom.sh \
    --script-builddeps "git curl jq rpmdevtools tar gzip" \
    --script-chroot fedora-latest-x86_64 --webhook-rebuild on
```

COPR begrenzt das Skript auf 4 kB. Änderungen an `lap.spec` und den anderen Dateien wirken nach `git push` ohne neues Eintragen.

Bau von Hand starten: `copr-cli build-package lap --name lap`

## Automatischer Bau bei neuen Releases

COPR erkennt neue Lap-Releases nicht selbst. Ein Webhook löst den Bau aus:

1. Die Webhook-Adresse steht in COPR unter „Settings“ → „Integrations“ → „Custom webhook“.
   Sie hat die Form `https://copr.fedorainfracloud.org/webhooks/custom/<ID>/<UUID>/lap/`.
2. Die Adresse ist geheim. Wer sie kennt, kann Bauten auslösen. Veröffentliche sie nicht.
3. Ein GitHub-Workflow im Repository von Lap ruft sie bei `release: published` auf und sendet `{"version": "<tag>"}`.
   Die Adresse liegt dort als Secret `COPR_WEBHOOK_URL`.

Erscheint eine neue Fedora-Version, füge den neuen Chroot hinzu, zum Beispiel:
`copr-cli modify lap --chroot fedora-44-x86_64 --chroot fedora-45-x86_64`

## Installieren

1. Binde das Repository ein: `sudo dnf copr enable beneedict/lap`
2. Installiere Lap: `sudo dnf install lap`

Updates kommen danach mit `sudo dnf upgrade`.

## Gesichtserkennung

Das RPM enthält die Gesichtsmodelle `det_500m.onnx` und `w600k_mbf.onnx` nicht.
Sie sind laut InsightFace nur für nicht-kommerzielle Forschung frei.
Ohne die Modelle startet Lap, aber die Gesichtserkennung ist aus.

1. Lade die Modelle: `sudo lap-face-models`
2. Starte Lap neu.

Das Skript prüft die SHA-256-Summen. `sudo lap-face-models --remove` entfernt die Modelle.
`dnf remove lap` entfernt sie ebenfalls.

## HEIC-Fotos (HEVC)

Das Paket enthält keinen HEVC-Decoder. Fedora und COPR dürfen ihn wegen Patenten nicht verteilen.
`copr-custom.sh` und `make-srpm.sh` entfernen deshalb `third_party/libde265` und `third_party/libheif` aus dem Quellarchiv.
`lap-system-libheif.patch` lässt Lap gegen die `libheif` des Systems linken.

Fedoras `libheif` kann kein HEVC. Für HEIC-Fotos (z. B. vom iPhone) installiere das Plugin aus RPM Fusion:
`sudo dnf install libheif-freeworld`

Ab der nächsten Lap-Version nach 0.3.2 ist die Option `LAP_SYSTEM_LIBHEIF` in Lap enthalten (PR #359).
`%prep` wendet den Patch deshalb nur an, wenn `src-tauri/build.rs` die Option noch nicht kennt.

## FFmpeg

Das RPM enthält kein FFmpeg. Lap nutzt `/usr/bin/ffmpeg` und `/usr/bin/ffprobe`.
Die Links liegen in `/usr/lib/Lap/ffmpeg/`.

- `ffmpeg` aus RPM Fusion: dekodiert HEVC (H.265). Empfohlen.
- `ffmpeg-free` aus Fedora: kein HEVC. Manche Handy-Videos zeigen kein Vorschaubild.

## Bekannte Punkte

- Das Tauri-Updater-Plugin in Lap kann ein RPM nicht aktualisieren. Updates kommen über COPR.
- Ohne `APTABASE_KEY` beim Bau ist die Telemetrie von Lap aus.
