# Park Go 4.3 — Windows

## Qué corrigió esta actualización

- El instalador ya **no busca Python 3.13** (no está instalado en tu equipo). Usa primero `python`, que en tu computadora es Python 3.15.1. Si no está disponible, prueba el Python predeterminado de `py -3`.
- Ya **no usa `uvicorn[standard]` ni PyYAML**, para evitar el intento de compilación con Visual C++.
- `requirements.txt` agrega `tzdata` y `app.py` utiliza un respaldo UTC-05:00 si faltaran los datos de `America/Bogota`.
- El `.bat` **detecta explícitamente** si quedó el `app.py` antiguo y no afirma que el servidor está listo hasta verificar que pueda importarse.

## Solución recomendada — instalar versión completa nueva

1. Detén cualquier ejecución previa (Ctrl+C en la ventana antigua).
2. Descomprime `ParkGo_4_3_Completo_Instalacion_Estable.zip` en una carpeta NUEVA (sin mezclar con archivos de versiones anteriores).
3. Abre la carpeta `ParkGo` extraída y haz doble clic en `iniciar_parkgo.bat`. Usará el Python 3.15 que ya tienes instalado; no se requiere instalar Python 3.13.
4. Cuando aparezca `[OK] Codigo, librerias y zona horaria cargados.`, abre `http://127.0.0.1:8000/` en tu navegador. Panel: `http://127.0.0.1:8000/business`.
5. Si tenías reservas o cuentas importantes en tu versión antigua, **con ambas aplicaciones apagadas**, copia solo `parkgo.db` de tu carpeta antigua a la nueva, reemplazando el archivo de demostración (si existe).

## Alternativa: reparar tu carpeta actual

1. Extrae los **3 archivos** del `ParkGo_4_3_Parche_Obligatorio_3_Archivos.zip`.
2. Copia `app.py`, `requirements.txt` e `iniciar_parkgo.bat` **directamente en la carpeta ParkGo donde está parkgo.db**. Acepta reemplazar los tres archivos. No los coloques dentro de una subcarpeta adicional.
3. Ejecuta `iniciar_parkgo.bat` desde esa carpeta.
4. No borres `parkgo.db`. No es necesario eliminar `.venv` salvo que el iniciador indique que está dañado.

## Si aparece un error, prueba en PowerShell desde la carpeta ParkGo

```powershell
.\.venv\Scripts\python.exe -m pip install tzdata
.\.venv\Scripts\python.exe -c "import app; print('IMPORTACION OK')"
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

El código ya se probó en Linux con Python 3.13. La ejecución específica del `.bat` con Windows y Python 3.15 debe comprobarse en tu PC.
