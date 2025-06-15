**Anweisungen zum Einrichten als Cronjob:**

1.  **Abhängigkeiten installieren:**
    ```bash
    pip install requests xarray psycopg2-binary pandas pyproj tqdm
    # Sie benötigen netcdf-Bibliotheken auf Ihrem System, z.B. unter Debian/Ubuntu:
    # sudo apt-get update && sudo apt-get install libnetcdf-dev
    ```
2.  **Skript ausführbar machen:**
    ```bash
    chmod +x importer.py
    ```
3.  **Cronjob editieren:** Öffnen Sie die Crontab-Datei Ihres Benutzers.
    ```bash
    crontab -e
    ```
4.  **Cronjob-Eintrag hinzufügen:** Fügen Sie die folgende Zeile hinzu, um das Skript jeden Tag um z.B. 3:00 Uhr morgens auszuführen. Passen Sie den Pfad zum Skript an.
    ```crontab
    # Führe den DWD-Datenimport jeden Tag um 3:00 Uhr aus
    0 3 * * * /usr/bin/python3 /pfad/zu/ihrem/projekt/importer.py >> /pfad/zu/ihrem/projekt/importer.log 2>&1
    ```
    * `>> /pfad/zu/ihrem/projekt/importer.log 2>&1` leitet alle Ausgaben (Standard und Fehler) in eine Log-Datei um, was für die Fehlersuche unerlässlich i