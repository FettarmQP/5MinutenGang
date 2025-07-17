# 🔊 Eigene Sounds verwenden

## Unterstützte Formate:
- **MP3** (empfohlen) - Gute Kompression, von allen Browsern unterstützt
- **WAV** - Hohe Qualität, größere Dateien
- **OGG** - Gute Kompression, von den meisten Browsern unterstützt
- **M4A** - Gute Qualität

## Sounds hinzufügen:

1. **Lokale Datei:**
   - Kopiere deine Sounddatei in den `static/` Ordner
   - Benenne sie z.B. `notification.mp3`
   - Aktiviere in `index.html`: `loadCustomSound('/static/notification.mp3');`

2. **Online Sound:**
   - Verwende eine URL: `loadCustomSound('https://example.com/sound.mp3');`

## Beispiele für kostenlose Sounds:
- **Freesound.org** - Kostenlose Sound-Effekte
- **Zapsplat.com** - Professionelle Sounds (kostenlose Registrierung)
- **Pixabay** - Kostenlose Musik und Sound-Effekte

## Empfohlene Sound-Eigenschaften:
- **Länge:** 0.5 - 2 Sekunden
- **Lautstärke:** Nicht zu laut (wird automatisch auf 70% reduziert)
- **Format:** MP3 für beste Kompatibilität
- **Dateigröße:** < 100KB für schnelles Laden

## Beispiel-Aktivierung in index.html:
```javascript
// Eine dieser Zeilen auskommentieren:
loadCustomSound('/static/notification.mp3');    // Lokale MP3 Datei
loadCustomSound('/static/ding.wav');           // Lokale WAV Datei
loadCustomSound('https://example.com/beep.mp3'); // Online Sound
```

## Sound-Lautstärke anpassen:
Die Lautstärke kann in der `loadCustomSound` Funktion angepasst werden:
```javascript
customAudio.volume = 0.5; // 50% Lautstärke (0.0 - 1.0)
```
