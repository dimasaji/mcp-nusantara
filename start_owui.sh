#!/bin/bash
# Start OpenWebUI dengan admin account yang benar
export WEBUI_ADMIN_EMAIL="admin@admin.com"
export WEBUI_ADMIN_PASSWORD="admin123"
export WEBUI_SECRET_KEY="$(openssl rand -base64 32)"

exec /c/Users/dmaza/AppData/Local/Programs/Python/Python311/python.exe "/c/Users/dmaza/AppData/Local/Programs/Python/Python311/Scripts/open-webui.exe" serve --host 0.0.0.0 --port 8080
