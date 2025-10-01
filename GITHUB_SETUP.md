# GitHub Setup Anleitung

## Schritt 1: GitHub Repository erstellen

1. Gehen Sie zu [GitHub.com](https://github.com) und loggen Sie sich ein
2. Klicken Sie auf "New repository" (grüner Button)
3. Füllen Sie die Details aus:
   - **Repository name**: `ebp-data-analysis` (oder ein anderer Name Ihrer Wahl)
   - **Description**: `EBP Data Ingestion Script - Optimized Python script for data extraction and analysis`
   - **Visibility**: Wählen Sie "Private" (empfohlen für sensible Daten)
   - **Initialize**: Lassen Sie "Add a README file" **NICHT** angehakt (wir haben bereits eine)

## Schritt 2: Repository mit lokalem Code verbinden

Führen Sie die folgenden Befehle in Ihrem Terminal aus:

```bash
# Navigieren Sie zum Projektverzeichnis
cd /Users/matthiasveitinger/Desktop/CKW/ebp_analysis

# Fügen Sie das GitHub Repository als Remote hinzu
# Ersetzen Sie USERNAME und REPO_NAME mit Ihren GitHub-Details
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# Benennen Sie den Hauptbranch zu 'main' um (falls nötig)
git branch -M main

# Laden Sie den Code hoch
git push -u origin main
```

## Schritt 3: Repository konfigurieren

### Secrets für GitHub Actions (optional)

Wenn Sie GitHub Actions verwenden möchten, fügen Sie diese Secrets hinzu:

1. Gehen Sie zu Ihrem Repository auf GitHub
2. Klicken Sie auf "Settings" → "Secrets and variables" → "Actions"
3. Fügen Sie folgende Secrets hinzu:
   - `EBP_USERNAME`: Ihr EBP Benutzername
   - `EBP_PASSWORD`: Ihr EBP Passwort
   - `EBP_BASE_URL`: Die EBP API URL
   - `EXPORT_BASE_PATH`: Der Export-Pfad

### Branch Protection (empfohlen)

1. Gehen Sie zu "Settings" → "Branches"
2. Klicken Sie "Add rule"
3. Wählen Sie "main" als Branch
4. Aktivieren Sie "Require pull request reviews before merging"

## Schritt 4: Projekt-Dokumentation

Das Repository enthält bereits:
- ✅ README.md mit vollständiger Dokumentation
- ✅ .env.example für Konfiguration
- ✅ requirements.txt für Dependencies
- ✅ .gitignore für sensible Dateien
- ✅ Test-Scripts für Validierung

## Sicherheitshinweise

⚠️ **Wichtig**: 
- Die `.env` Datei ist in `.gitignore` enthalten und wird NICHT hochgeladen
- Verwenden Sie `.env.example` als Vorlage für andere Entwickler
- Verwenden Sie GitHub Secrets für sensible Daten in CI/CD
- Stellen Sie sicher, dass das Repository privat ist

## Nächste Schritte

Nach dem Hochladen können Sie:
1. Issues für Bug-Reports erstellen
2. Pull Requests für Code-Änderungen verwenden
3. GitHub Actions für automatische Tests einrichten
4. Releases für Versionierung erstellen
