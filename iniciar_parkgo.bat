@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Park Go 4.3 - Inicio estable para Windows

 echo.
echo ====================================================
echo   PARK GO - Tu espacio, a un clic de distancia.
echo   Conductores + Park Go Business
echo ====================================================
 echo.

rem IMPORTANT: open this .bat from the SAME directory as app.py.
if not exist "app.py" goto missing_files
if not exist "requirements.txt" goto missing_files
rem Previous partial patches only replaced this BAT, not app.py.
findstr /C:"except ZoneInfoNotFoundError" "app.py" >nul 2>nul
if errorlevel 1 goto outdated_app

set "VENV_PY=%CD%\.venv\Scripts\python.exe"
if exist "%VENV_PY%" goto check_venv

echo [INFO] No hay entorno virtual. Buscando el Python que YA tienes instalado...
rem Uses `python` first (on your machine: Python 3.15.1); no fixed py -3.13.
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if not errorlevel 1 goto create_with_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if not errorlevel 1 goto create_with_py

echo [ERROR] No se encontro un Python 3.11 o superior.
echo Abre PowerShell, ejecuta: python --version
echo Si python funciona en PowerShell pero no aqui, revisa el PATH.
goto failed

:create_with_python
echo [INFO] Creando .venv con Python instalado:
python --version
python -m venv ".venv"
if errorlevel 1 goto failed_venv
goto check_venv

:create_with_py
echo [INFO] Creando .venv con el Python por defecto del iniciador:
py -3 --version
py -3 -m venv ".venv"
if errorlevel 1 goto failed_venv
goto check_venv

:check_venv
"%VENV_PY%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 goto broken_venv
echo [OK] Python del entorno virtual:
"%VENV_PY%" --version
if errorlevel 1 goto broken_venv

"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 goto missing_pip

echo.
echo [INFO] Comprobando dependencias...
"%VENV_PY%" -m pip install --disable-pip-version-check --prefer-binary -r "requirements.txt"
if errorlevel 1 goto failed_deps

echo.
echo [INFO] Validando codigo y zona horaria antes de arrancar...
"%VENV_PY%" -c "import app; print('[OK] Codigo, librerias y zona horaria cargados.')"
if errorlevel 1 goto failed_import

echo.
echo ====================================================
echo   Conductores: http://127.0.0.1:8000/
echo   Operador:    http://127.0.0.1:8000/business
echo ====================================================
echo [OK] Ejecutando servidor. No cierres esta ventana.
echo Pulsa Ctrl+C para detenerlo.
echo.
"%VENV_PY%" -m uvicorn app:app --host 127.0.0.1 --port 8000
if errorlevel 1 goto failed_server
goto end

:missing_files
echo [ERROR] Debes ejecutar iniciar_parkgo.bat dentro de la carpeta ParkGo.
echo Faltan app.py o requirements.txt. Extrae TODO el ZIP primero.
goto failed

:outdated_app
echo [ERROR] Detecte el app.py antiguo. NO copies solo el archivo .bat.
echo Copia app.py, requirements.txt e iniciar_parkgo.bat JUNTOS
echo sobre la carpeta antigua ParkGo, reemplazando los 3 archivos.
goto failed

:broken_venv
echo [ERROR] Tu entorno .venv esta danado o es incompatible.
echo Cierra esta ventana; renombra SOLO .venv a .venv_anterior.
echo Despues ejecuta otra vez este mismo .bat. NO borres parkgo.db.
goto failed

:missing_pip
echo [ERROR] pip no esta disponible en el entorno virtual.
echo Prueba: .venv\Scripts\python.exe -m ensurepip --upgrade
goto failed

:failed_venv
echo [ERROR] No pude crear el entorno. No hay una version fija exigida.
echo Se admite el Python 3.15.1 que ya tienes instalado.
goto failed

:failed_deps
echo [ERROR] Fallo la instalacion de librerias. No arranco el servidor.
echo Prueba con conexion a internet y confirma que requirements.txt esta actualizado.
goto failed

:failed_import
echo [ERROR] El codigo o una dependencia no se pudo cargar.
echo Revisa el error justo arriba. El servidor NO se ha iniciado.
goto failed

:failed_server
echo [ERROR] El servidor termino con error. Revisa el mensaje de arriba.
echo Si el puerto 8000 esta ocupado, cierra otras instancias de Park Go.
goto failed

:failed
echo.
echo AVISO: Tus reservas y cuentas siguen en parkgo.db.
pause
exit /b 1

:end
pause
exit /b 0
