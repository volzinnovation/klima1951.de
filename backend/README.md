**Anweisungen zur Ausführung des Backends:**

1.  **Abhängigkeiten installieren:** Speichern Sie die FastAPI-Anwendung als `main.py` und erstellen Sie eine `requirements.txt`-Datei im selben Verzeichnis:
    ```
    # requirements.txt
    fastapi
    uvicorn
    asyncpg
    geopy
    ```
    Installieren Sie diese dann mit:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Server starten:** Führen Sie den Server aus dem Terminal aus:
    ```bash
    uvicorn main:app --reload
    ```
    * `--reload` sorgt dafür, dass der Server bei Code-Änderungen automatisch neu startet, was sehr praktisch für die Entwicklung ist.

Ihre API ist nun unter `http://127.0.0.1:8000` erreichbar. Sie können die interaktive API-Dokumentation unter `http://127.0.0.1:8000/docs` aufrufen, um die Endpunkte zu testen.

Vergessen Sie nicht, in Ihrer Frontend-Anwendung die API-Aufrufe von den simulierten Daten auf diese neuen Backend-Endpunkte umzustell