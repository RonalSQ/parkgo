# Park Go 4.2 — corrección de zona horaria en Windows

## ¿Cuál era el error?

Al iniciar la versión 4.1 con Python 3.15 en Windows, `ZoneInfo('America/Bogota')` podía fallar con `No module named 'tzdata'` y `ZoneInfoNotFoundError`. La aplicación requiere datos IANA de zonas horarias, que Windows no siempre proporciona a Python.

## Solución más rápida si conservas la carpeta actual

En PowerShell, dentro de la carpeta `ParkGo`, ejecuta:

```powershell
.\.venv\Scripts\python.exe -m pip install tzdata
```

Después ejecuta `iniciar_parkgo.bat` de nuevo.

## Solución permanente

Si ya estás usando la versión 4.1, copia desde el parche 4.2 los archivos `app.py`, `requirements.txt` e `iniciar_parkgo.bat` sobre la carpeta actual `ParkGo`. **NO reemplaces ni borres `parkgo.db`**, pues contiene reservas y cuentas creadas localmente. No es necesario borrar `.venv`.

La 4.2 añade `tzdata` a las dependencias y, como protección adicional, usa UTC-05:00 si Python no consigue cargar `America/Bogota`. Colombia no usa horario de verano, por lo que el horario de reservas seguirá siendo correcto.

## Ejecutar

Inicia `iniciar_parkgo.bat` y entra a:

- Conductores: http://127.0.0.1:8000/
- Parqueaderos / operador: http://127.0.0.1:8000/business

Si tienes una copia de datos anterior y deseas usar la carpeta nueva, copia tu `parkgo.db` a la carpeta `ParkGo` nueva con el servidor detenido.

**Nota:** se comprobó el arranque y las pruebas del código con Python 3.13 en Linux; el `.bat` de Windows y Python 3.15 deben verificarse en el propio computador. El parche evita que el código de zona horaria impida arrancar incluso si `tzdata` no está disponible.
