# ADR 0001: Eine zentrale .env im Root

- **Status:** vorgeschlagen (auf "akzeptiert" setzen, sobald das Team zugestimmt hat)
- **Datum:** 2026-10-14

## Kontext

Das Projekt ist ein Monorepo mit `backend/` (FastAPI), `frontend/` (React)
und einer Datenbank, die über Docker Compose gemeinsam gestartet werden.
Für Zugangsdaten und Konfiguration (z. B. DB-Passwort, Schlüssel für
Authentifizierung) braucht es Umgebungsvariablen. Das Repository ist
öffentlich, Secrets dürfen daher nie committet werden.

## Entscheidung

Es gibt genau eine `.env` im Projekt-Root. Sie wird nicht versioniert.
Stattdessen liegt eine `.env.example` mit Platzhaltern im Repo.
Docker Compose gibt jedem Service per `environment:` nur die Variablen
weiter, die dieser benötigt. Das Frontend erhält ausschließlich
öffentliche Werte (z. B. die API-URL).

Die Root-`.gitignore` enthält dafür:

    .env
    .env.*
    !.env.example

## Begründung

- Gemeinsame Werte (z. B. DB-Zugangsdaten für Datenbank und Backend)
  stehen an einer Stelle und können nicht auseinanderlaufen.
- Geringer Pflegeaufwand für ein kleines Team in Phase 0.
- Das Sicherheitsprinzip "Least Privilege" wird über die explizite
  Weitergabe pro Service umgesetzt, nicht über getrennte Dateien.

## Konsequenzen

- Positiv: ein zentraler Ort, einfaches Onboarding über `.env.example`.
- Negativ: Wird die Datei pauschal per `env_file:` an alle Container
  durchgereicht, haben alle Zugriff auf alle Werte. Das ist zu vermeiden.
- Lokale Entwicklung des Backends ohne Docker erwartet ggf. eine `.env`
  im Backend-Ordner. Das ist bei Bedarf zu lösen (siehe Alternativen).

## Verworfene Alternative

Eine `.env` pro Ordner (`backend/.env`, `frontend/.env`): bessere
Trennung der Zuständigkeiten, aber Doppelpflege gemeinsamer Werte und
höheres Fehlerrisiko. Kann später nachgezogen werden, falls die
Konfiguration pro Service deutlich wächst.