@echo off
chcp 65001 >nul
echo ============================================
echo   MemeVault - Hizli Baslatma
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] Docker (PostgreSQL, Redis, MinIO) baslatiliyor...
docker-compose -f backend\docker-compose.yml up -d postgres redis minio
timeout /t 5 /nobreak >nul

echo.
echo [2/4] Veritabani migration (ilk kurulumda)...
cd backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo UYARI: venv yok. "python -m venv venv" ve "pip install -r requirements.txt" calistirin.
    pause
    exit /b 1
)
set PYTHONPATH=%CD%
alembic upgrade head
cd ..

echo.
echo ============================================
echo   Asagidaki 3 islemi AYRI terminallerde acin:
echo ============================================
echo.
echo   TERMINAL 1 - Backend API:
echo   cd backend
echo   venv\Scripts\activate
echo   set PYTHONPATH=%CD%
echo   uvicorn app.main:app --reload
echo.
echo   TERMINAL 2 - Celery Worker (video isleme):
echo   cd backend
echo   venv\Scripts\activate
echo   set PYTHONPATH=%CD%
echo   celery -A app.workers.celery_app worker --loglevel=info --pool=solo
echo.
echo   TERMINAL 3 - Frontend:
echo   cd frontend
echo   npm run dev
echo.
echo   Tarayici: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ============================================
pause
