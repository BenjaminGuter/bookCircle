# Git-Handout

Dieses Handout erklärt die Grundlagen von Git und den Umgang mit einem
gemeinsamen Repository im Team. Es wurde im Team über Branches und
Pull Requests erstellt.

## Inhalt

1. [Was ist Git und warum sollte man es verwenden?](#1-was-ist-git-und-warum-sollte-man-es-verwenden)
2. [Grundlegende Git-Befehle](#2-grundlegende-git-befehle)
3. [Branches und Merge-Konflikte](#3-branches-und-merge-konflikte)
4. [Git mit IntelliJ / PyCharm](#4-git-mit-intellij--pycharm)
5. [Nützliche Git-Tools und Plattformen](#5-nützliche-git-tools-und-plattformen)
6. [Beiträge der Teammitglieder](#6-beiträge-der-teammitglieder)

---

## 1. Was ist Git und warum sollte man es verwenden?

(Jana ergänzen per commit)

---

## 2. Grundlegende Git-Befehle

### Die vier Orte, an denen sich Änderungen befinden

```
Arbeitsverzeichnis --git add--> Staging-Bereich --git commit--> Lokales Repository --git push--> Remote-Repository
```

- **Arbeitsverzeichnis:** die Dateien, an denen man gerade arbeitet.
- **Staging-Bereich:** Sammelstelle für Änderungen, die in den nächsten
  Commit aufgenommen werden sollen.
- **Lokales Repository:** die Historie auf dem eigenen Rechner.
- **Remote-Repository:** die gemeinsame Kopie auf einer Plattform wie GitHub.

### Einmalige Einrichtung

```
git config --global user.name "Vorname Nachname"
git config --global user.email "name@example.com"
```

Name und E-Mail-Adresse werden in jedem Commit gespeichert.

### Befehlsübersicht

| Befehl | Wirkung | Beispiel |
|--------|---------|----------|
| `git init` | Legt in einem Ordner ein neues, leeres lokales Repository an. | `git init` |
| `git clone <url>` | Kopiert ein bestehendes Remote-Repository samt Historie in einen neuen Ordner und richtet `origin` automatisch ein. | `git clone https://github.com/user/projekt.git` |
| `git status` | Zeigt, welche Dateien geändert, vorgemerkt oder noch nicht versioniert sind. | `git status` |
| `git add <datei>` | Merkt Änderungen für den nächsten Commit vor (Staging). | `git add README.md` |
| `git commit -m "<text>"` | Speichert die vorgemerkten Änderungen als Commit im lokalen Repository. | `git commit -m "docs: add section on branches"` |
| `git push` | Überträgt lokale Commits ins Remote-Repository. Beim ersten Push eines neuen Branches: `git push -u origin <branch>`. | `git push -u origin docs/handout-branches` |
| `git pull` | (Maxi ausfüllen per commit) | |
| `git log` | (Jana ausfüllen per commit) | |
| `git diff` | Zeigt Änderungen im Arbeitsverzeichnis, die noch nicht gestaged sind. Mit `--staged` die vorgemerkten Änderungen. | `git diff --staged` |

### Typischer Ablauf

```
git status                       # Was hat sich geändert?
git add datei.md                 # Änderung vormerken
git diff --staged                # Vorgemerkte Änderung prüfen
git commit -m "docs: add intro"  # Festhalten
git push                         # Ins Remote-Repository übertragen
```

### Gute Commits

- Ein Commit sollte **eine zusammengehörende Änderung** enthalten.
- Die Nachricht beschreibt, **was und warum** geändert wurde, und steht
  im Imperativ (z. B. `add`, `fix`, nicht `added`).
- Dateien, die nicht ins Repository gehören (Passwörter, `.env`-Dateien,
  Build-Ordner, IDE-Einstellungen), werden über eine `.gitignore`
  ausgeschlossen. Wichtig: Was einmal committet wurde, bleibt in der
  Historie, auch wenn es später gelöscht wird.

---

## 3. Branches und Merge-Konflikte

### Was ist ein Branch?

Ein Branch ist eine **eigene Entwicklungslinie**. Man arbeitet darin an
einer Aufgabe, ohne den stabilen Hauptstand (`main`) zu verändern.
Ist die Arbeit fertig, wird der Branch in `main` zusammengeführt
(**Merge**).

**Warum Branches?**

- Jede Person kann parallel an etwas anderem arbeiten.
- `main` bleibt stabil und lauffähig.
- Änderungen lassen sich vor dem Zusammenführen prüfen (Review).

### Wichtige Befehle

| Befehl | Wirkung |
|--------|---------|
| `git branch` | Listet lokale Branches, der aktive ist markiert. |
| `git switch -c <name>` | Legt einen neuen Branch an und wechselt direkt hinein. |
| `git switch <name>` | Wechselt auf einen bestehenden Branch. |
| `git merge <name>` | Führt den genannten Branch in den aktuell aktiven zusammen. |
| `git branch -d <name>` | Löscht einen Branch, der bereits gemerged wurde. |

Ältere Git-Versionen kennen `git switch` noch nicht. Dort entspricht
`git checkout -b <name>` bzw. `git checkout <name>` dem gleichen Zweck.

### Arbeitsablauf mit Pull Requests

1. Neuen Branch von `main` anlegen: `git switch -c docs/mein-thema`
2. Änderungen vornehmen und in mehreren kleinen Commits festhalten.
3. Branch pushen: `git push -u origin docs/mein-thema`
4. Auf der Plattform einen **Pull Request (PR)** von diesem Branch nach
   `main` eröffnen.
5. Teammitglieder prüfen die Änderungen (**Review**), kommentieren und
   genehmigen sie.
6. Nach der Freigabe wird der PR in `main` gemerged.

Branch-Namen sollten sprechend sein und einer Konvention folgen,
z. B. `docs/handout-branches` oder `feature/book-search`.

### Merge-Konflikte

Ein Konflikt entsteht, wenn zwei Branches **dieselbe Stelle einer Datei**
unterschiedlich verändert haben und Git nicht entscheiden kann, welche
Version gelten soll. Das ist normal und kein Fehler.

Git markiert die betroffene Stelle in der Datei:

```
<<<<<<< HEAD
Version aus dem aktuellen Branch
=======
Version aus dem Branch, der gemerged wird
>>>>>>> docs/andere-branch
```

**So wird ein Konflikt gelöst:**

1. `git status` zeigt, welche Dateien betroffen sind (`both modified`).
2. Datei öffnen und entscheiden: eine Version behalten, die andere
   behalten oder beide sinnvoll kombinieren.
3. Die Markierungen `<<<<<<<`, `=======` und `>>>>>>>` vollständig
   entfernen.
4. Datei mit `git add <datei>` als gelöst markieren.
5. Den Merge mit `git commit` abschließen.

Wer den Merge lieber abbrechen möchte, kann mit `git merge --abort`
zum Stand vor dem Merge zurückkehren.

**Konflikte vermeiden:**

- Kleine Änderungen und regelmäßig in `main` integrieren.
- Im Team absprechen, wer an welcher Datei oder welchem Abschnitt
  arbeitet.
- Vor Beginn neuer Arbeit den aktuellen Stand von `main` holen.

---

## 4. Git mit IntelliJ / PyCharm

IntelliJ IDEA und PyCharm haben Git-Unterstützung eingebaut, man muss
nicht zwingend die Kommandozeile verwenden. Die Menüs unterscheiden sich
je nach Version leicht (ältere Versionen zeigen das Menü als **VCS**,
neuere als **Git**).

### Local Repository und Remote Repository

- Das **Local Repository** liegt auf dem eigenen Rechner im Projektordner
  (versteckter Ordner `.git`). Commits landen zunächst nur dort.
- Das **Remote Repository** liegt auf einer Plattform wie GitHub und wird
  über einen Namen angesprochen, standardmäßig `origin`.
- Zwischen beiden wird per **Push** (lokal nach remote) und **Pull** bzw.
  **Update** (remote nach lokal) synchronisiert.

### Wichtige Funktionen

| Aufgabe | Vorgehen in der IDE |
|---------|---------------------|
| Projekt aus Remote holen | Beim Start bzw. im Menü *Get from Version Control* bzw. *Clone* wählen und die Repository-URL eingeben. |
| Bestehendes Projekt unter Versionskontrolle stellen | Im Menü *Git* bzw. *VCS* die Option zum Anlegen eines Git-Repositorys wählen. |
| Änderungen committen | Fenster **Commit** öffnen (Standard-Tastenkürzel `Strg+K`), Dateien auswählen, Nachricht schreiben, *Commit*. |
| Änderungen pushen | Menü *Git → Push* (Standard-Tastenkürzel `Strg+Shift+K`). |
| Änderungen vom Remote holen | Menü *Git → Pull* bzw. *Update Project*. |
| Branch wechseln oder anlegen | Branch-Anzeige in der Titel- bzw. Statusleiste anklicken, dann *New Branch* oder einen Branch auswählen. |
| Konflikte lösen | Bei einem Konflikt öffnet die IDE einen Merge-Dialog mit drei Ansichten (links eigene Version, rechts die andere, in der Mitte das Ergebnis). |
| Historie ansehen | Fenster **Git** bzw. **Version Control** mit dem Reiter *Log*. |
| Remote verwalten | Menü *Git → Manage Remotes*. |

Dateien, die nicht versioniert werden sollen, trägt man in die
`.gitignore` ein. Die IDE zeigt ignorierte Dateien in der Projektansicht
farblich abgesetzt an.

Ein Konto der Plattform (z. B. GitHub) lässt sich in den Einstellungen
unter *Version Control* hinterlegen, damit Push und Clone ohne manuelle
Zugangsdaten funktionieren.

---

## 5. Nützliche Git-Tools und Plattformen

(Maxi ergänzen per commit)

---

## 6. Beiträge der Teammitglieder

| Teammitglied | Beitrag |
|--------------|---------|
| Ben | Kapitel 2 / 3 / 4|
| Maxi | Kapitel 5 |
| Jana | Kapitel 1 |