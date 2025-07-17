# 5MinutenGang - Twitch Chatter Welcome Display

Eine Flask-Webapp, die in den ersten 5 Minuten eines Twitch-Streams alle Chatter sammelt und sie dann rotierend als Willkommensgruß anzeigt. Perfekt für OBS Integration!

## Features

- 🎮 **Twitch Chat Integration** - Sammelt Chatter in den ersten 5 Minuten
- 🖼️ **Profilbilder** - Zeigt Twitch-Avatare der Chatter
- 🔄 **Rotierende Anzeige** - Wechselt alle 5 Sekunden zwischen Chattern
- 🎨 **Transparenter Hintergrund** - Perfekt für OBS
- 📱 **Responsive Design** - Funktioniert auf allen Bildschirmgrößen
- ⚡ **Real-time Updates** - WebSocket-basierte Live-Updates

## Installation

1. **Repository klonen:**
```bash
git clone https://github.com/FettarmQP/5MinutenGang.git
cd 5MinutenGang
```

2. **Virtual Environment erstellen:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# oder
source venv/bin/activate  # Linux/Mac
```

3. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

4. **Umgebungsvariablen konfigurieren:**
Erstelle eine `.env` Datei:
```env
TWITCH_CLIENT_ID=deine_twitch_client_id
TWITCH_ACCESS_TOKEN=dein_twitch_access_token
TWITCH_CHANNEL=dein_kanal_name
```

## Twitch API Setup

1. Gehe zu [Twitch Developers](https://dev.twitch.tv/console)
2. Erstelle eine neue Anwendung
3. Notiere dir die Client ID
4. Generiere einen Access Token mit Chat-Berechtigung

## Verwendung

1. **Server starten:**
```bash
python app.py
```

2. **Browser öffnen:**
Gehe zu `http://localhost:5000`

3. **In OBS einbinden:**
- Quelle hinzufügen → Browser-Quelle
- URL: `http://localhost:5000`
- Breite: 400px, Höhe: 300px (oder nach Wunsch anpassen)

## Steuerung

### Web-Interface
- **Start Sammlung** - Beginnt die 5-Minuten Sammlung
- **Stop Sammlung** - Stoppt die Sammlung vorzeitig
- **Controls ausblenden** - Versteckt die Steuerung für OBS

### Keyboard Shortcuts
- `Ctrl + S` - Sammlung starten
- `Ctrl + X` - Sammlung stoppen  
- `Ctrl + H` - Controls ein/ausblenden

### API Endpoints
- `GET /` - Hauptseite
- `GET /start_collection` - Sammlung starten
- `GET /stop_collection` - Sammlung stoppen
- `GET /status` - Aktueller Status

## Funktionsweise

1. **Sammlung (5 Minuten)**: App sammelt alle einzigartigen Chatter
2. **Warteschlange**: Jeder Chatter wird nur einmal erfasst
3. **Anzeige**: Rotiert alle 5 Sekunden durch die Chatter
4. **Profilbilder**: Lädt automatisch Twitch-Avatare

## Anpassungen

### Zeitintervalle ändern
In `app.py`:
```python
# Sammlungszeit (aktuell 5 Minuten)
end_time = stream_start_time + timedelta(minutes=5)

# Anzeigeintervall (aktuell 5 Sekunden)
time.sleep(5)
```

### Styling anpassen
Bearbeite `templates/index.html` CSS-Abschnitt für:
- Farben und Gradients
- Animationen
- Layout und Größen

### Mock-Daten für Tests
Die App enthält Mock-Chatter für Tests. Für echte Twitch-Integration implementiere IRC-WebSocket-Verbindung.

## Struktur

```
5MinutenGang/
├── app.py              # Haupt-Flask-Anwendung
├── templates/
│   └── index.html      # Frontend Template
├── requirements.txt    # Python Dependencies
├── .env               # Umgebungsvariablen (nicht committen!)
└── README.md          # Diese Datei
```

## Troubleshooting

### Häufige Probleme

**Keine Chatter werden angezeigt:**
- Überprüfe Twitch API Credentials
- Stelle sicher, dass der Channel-Name korrekt ist
- Prüfe die Konsole auf Fehlermeldungen

**OBS zeigt nichts an:**
- Stelle sicher, dass der Server läuft
- Prüfe die Browser-Quelle URL
- Aktiviere "Control audio via OBS" in den Browser-Quelle Einstellungen

**Profilbilder laden nicht:**
- Internetverbindung prüfen
- Fallback auf Standard-Avatar ist implementiert

## Erweiterungsmöglichkeiten

- [ ] Echte Twitch IRC Integration
- [ ] Sound-Effekte bei neuen Chattern
- [ ] Verschiedene Themes/Layouts
- [ ] Chat-Nachrichten anzeigen
- [ ] Statistiken und Analytics
- [ ] Multi-Channel Support

## Lizenz

MIT License - siehe LICENSE Datei für Details.

## Support

Bei Fragen oder Problemen erstelle ein Issue auf GitHub oder kontaktiere @FettarmQP.

---

**Viel Spaß beim Streamen! 🎮✨**
