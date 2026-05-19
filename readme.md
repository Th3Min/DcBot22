# ⚡ XP Leveling Bot – Anleitung (Railway + PostgreSQL)

---

## Dateien im Überblick

```
xp-bot/
├── bot.py            ← Der Bot
├── Sync.py           ← Slash Commands manuell syncen (optional)
├── Procfile          ← Railway Startbefehl
├── requirements.txt  ← Python Pakete
├── runtime.txt       ← Python Version
└── ANLEITUNG.md      ← Diese Datei
```

---

## Schritt 1 – Bot auf Discord erstellen

1. Geh auf **https://discord.com/developers/applications**
2. Oben rechts **"New Application"** → Namen eingeben → **Create**
3. Links auf **"Bot"** klicken
4. **"Reset Token"** → Token kopieren und sicher aufbewahren ⚠️
5. Unter **"Privileged Gateway Intents"** aktivieren:
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT
6. **"Save Changes"**

---

## Schritt 2 – Bot einladen

Diesen Link im Browser öffnen (Client ID ersetzen):

```
https://discord.com/oauth2/authorize?client_id=DEINE_CLIENT_ID&permissions=8&scope=bot%20applications.commands
```

> ⚠️ Beide Scopes (`bot` UND `applications.commands`) müssen im Link sein, sonst funktionieren Slash Commands nicht!

---

## Schritt 3 – Railway einrichten

1. Geh auf **https://railway.app** → Login mit GitHub
2. **"New Project"** → **"Deploy from GitHub repo"** → dein Repo auswählen
3. Railway erkennt den `Procfile` automatisch

---

## Schritt 4 – Datenbank hinzufügen

1. Im Railway Projekt auf **"+ New"** klicken
2. **"Database"** → **"PostgreSQL"** wählen
3. Railway erstellt die DB automatisch
4. Auf die PostgreSQL-Instanz klicken → **"Variables"** → `DATABASE_URL` kopieren

---

## Schritt 5 – Umgebungsvariablen setzen

Im Railway Bot-Service auf **"Variables"** klicken und eintragen:

| Variable | Wert |
|---|---|
| `BOT_TOKEN` | Dein Bot Token aus Schritt 1 |
| `DATABASE_URL` | Automatisch von Railway gesetzt wenn du die DB im selben Projekt hast |

---

## Schritt 6 – Deployen

Railway deployed automatisch sobald du etwas in dein Repo pushst.  
Im **"Deployments"** Tab siehst du den Log – wenn dort steht:

```
✅ DB verbunden – X User | XP-Cooldown=20s
✅ 3 Slash Commands synchronisiert!
✅ Bot bereit als BotName#1234
```

→ alles läuft! 🎉

---

## Commands

| Command | Funktion |
|---|---|
| `/rang` | Dein Level, Titel, XP und Fortschrittsbalken |
| `/rang @mitglied` | Rang eines anderen Mitglieds |
| `/top` | Top-10 Rangliste |
| `/top 2` | Seite 2 der Rangliste |
| `/xpinfo` | Erklärt das XP-System |

---

## XP-System

- **XP pro Nachricht:** 15–25 (zufällig)
- **XP-Cooldown:** 20 Sekunden (Nachrichten werden trotzdem immer gezählt!)
- **Nachrichten-Counter:** kein Cooldown, zählt jede Nachricht

## Titel

| Level | Titel |
|---|---|
| 1–9 | 🟢 Anfänger |
| 10–19 | 🔵 Smalltalker |
| 20–29 | 🔴 Aggressiv Hängengeblieben |
| 30+ | 💀 Ultimativer Blindermann Hater |

---

## Häufige Fehler

**Slash Commands erscheinen nicht**  
→ Bot war beim Einladen ohne `applications.commands` scope → neu einladen mit dem Link aus Schritt 2

**`DATABASE_URL` nicht gesetzt**  
→ PostgreSQL im selben Railway Projekt hinzufügen, Railway setzt die Variable automatisch

**Bot startet nicht**  
→ Logs in Railway unter "Deployments" checken
