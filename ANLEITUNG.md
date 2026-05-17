# ⚡ XP Leveling Bot – Komplette Anleitung

---

## Schritt 1 – Python installieren

1. Geh auf **https://www.python.org/downloads**
2. Klick auf den großen gelben **"Download Python"** Button
3. Installiere es – wichtig: ✅ **"Add Python to PATH"** anhaken!
4. Nach der Installation: öffne die **Eingabeaufforderung** (Windows-Taste → "cmd" tippen → Enter)
5. Tippe `python --version` → es sollte sowas wie `Python 3.12.x` erscheinen

---

## Schritt 2 – discord.py installieren

In der Eingabeaufforderung (cmd) diesen Befehl eingeben und Enter drücken:

```
pip install discord.py
```

Warten bis es fertig ist ✅

---

## Schritt 3 – Bot auf Discord erstellen

1. Geh auf **https://discord.com/developers/applications**
2. Oben rechts auf **"New Application"** klicken
3. Einen Namen eingeben (z.B. "XP Bot") → **Create**
4. Links auf **"Bot"** klicken
5. Klick auf **"Reset Token"** → Token kopieren und irgendwo zwischenspeichern ⚠️ (zeigt er nur einmal!)
6. Weiter unten unter **"Privileged Gateway Intents"** diese zwei Schalter anmachen:
   - ✅ **SERVER MEMBERS INTENT**
   - ✅ **MESSAGE CONTENT INTENT**
7. Ganz unten auf **"Save Changes"** klicken

---

## Schritt 4 – Bot zum Server einladen

1. Links auf **"OAuth2"** → dann **"URL Generator"**
2. Unter **"Scopes"** den Haken bei **"bot"** setzen
3. Unter **"Bot Permissions"** diese anklicken:
   - ✅ Send Messages
   - ✅ View Channels
   - ✅ Embed Links
4. Den generierten Link unten kopieren → im Browser öffnen
5. Deinen Server auswählen → **Autorisieren**

---

## Schritt 5 – Token eintragen

1. Öffne die Datei **`bot.py`** mit einem Texteditor (z.B. Notepad oder VS Code)
2. Suche ganz oben diese Zeile:
   ```python
   BOT_TOKEN = "DEIN_TOKEN_HIER"
   ```
3. Ersetze `DEIN_TOKEN_HIER` mit deinem Token aus Schritt 3, z.B.:
   ```python
   BOT_TOKEN = "MTIzNDU2Nzg5.AbCdEf.xyz123..."
   ```
4. Speichern

---

## Schritt 6 – Bot starten

1. Öffne die Eingabeaufforderung (cmd)
2. Navigiere in den Ordner wo `bot.py` liegt, z.B.:
   ```
   cd Downloads\xp-bot
   ```
3. Bot starten:
   ```
   python bot.py
   ```
4. Wenn im Terminal steht `✅ XP Bot#1234 ist online!` → alles gut! 🎉

> ⚠️ Das cmd-Fenster muss **offen bleiben** solange der Bot laufen soll.

---

## Commands im Discord

| Command | Was macht er? |
|---|---|
| `/rang` | Zeigt dein Level, Titel, XP und Fortschrittsbalken |
| `/rang @mitglied` | Zeigt den Rang eines anderen Mitglieds |
| `/top` | Zeigt die Top-10 Rangliste |
| `/top 2` | Seite 2 der Rangliste |
| `/xpinfo` | Erklärt das XP-System |

> 💡 Slash Commands erscheinen automatisch wenn du `/` im Chat tippst!

---

## Titel-System

| Level | Titel |
|---|---|
| 1 – 9 | 🟢 Anfänger |
| 10 – 19 | 🔵 Smalltalker |
| 20 – 29 | 🔴 Aggressiv Hängengeblieben |
| 30+ | 💀 Ultimativer Blindermann Hater |

---

## Dateien im Überblick

```
xp-bot/
├── bot.py         ← Der Bot (hier Token eintragen)
├── requirements.txt
├── ANLEITUNG.md   ← Diese Datei
└── data.json      ← Wird automatisch erstellt wenn jemand schreibt
```

---

## Häufige Fehler

**"python wird nicht erkannt"**
→ Python nochmal installieren, diesmal ✅ "Add to PATH" anhaken

**"ModuleNotFoundError: discord"**
→ `pip install discord.py` nochmal ausführen

**Bot ist online aber Slash Commands erscheinen nicht**
→ Warte 1–2 Minuten nach dem ersten Start, Discord synchronisiert die Commands einmalig
→ Prüfe ob "MESSAGE CONTENT INTENT" im Developer Portal an ist

**Bot antwortet doppelt**
→ Stelle sicher dass du den Bot nur einmal gestartet hast
