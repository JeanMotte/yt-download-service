Launch the project

1. Start by renaming .devcontainer.example to .devcontainer.env
2. Fill the env variables
3. Ctrl+Shift+P -> Reopen and Build the container
4. poetry run uvicorn yt_download_service.main:app --host 0.0.0.0 --port 8000

---

Open api services

1. Openapi file available at http://localhost:8000/docs
