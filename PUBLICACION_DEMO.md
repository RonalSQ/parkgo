# Park Go: publicar la demo en GitHub + Render

Esta edición incluye **un solo parqueadero ficticio** y una base de datos `parkgo.db` sin usuarios registrados ni reservas.

## Paso 1: GitHub
1. Crea un nuevo repositorio llamado `parkgo-demo` en https://github.com/new (preferiblemente **privado**, si Render tiene acceso).
2. Sube **el contenido de esta carpeta**, no el archivo ZIP, a la **raíz** del repositorio.
3. Verifica que `app.py`, `requirements.txt` y `render.yaml` estén directamente en la raíz.

## Paso 2: Render
1. Conecta GitHub en Render y selecciona el repositorio recién creado.
2. Crea un Blueprint desde `render.yaml` o un Web Service (runtime Python, plan Free).
3. Introduce un correo de operador y una contraseña **nueva de 12+ caracteres** en `PARKGO_ADMIN_EMAIL` y `PARKGO_ADMIN_PASSWORD`.
4. `SECRET_KEY` se genera automáticamente si usas Blueprint.
5. Finaliza el despliegue y espera a que Render indique **Live**.
6. Abre `https://NOMBRE-REAL.onrender.com/` para conductores y `https://NOMBRE-REAL.onrender.com/business` para el operador.

## Advertencias
- El plan gratis **NO garantiza que SQLite conserve datos tras reinicios, suspensión o redespliegues**. Esta edición es solo para presentar en clase con cuentas ficticias.
- No uses datos personales reales y no compartas la contraseña de operador.
- Las imágenes y la ubicación inicial del parqueadero son de demostración. No se procesan pagos reales.
- No publiques contraseñas ni llaves en GitHub; Render gestiona variables de entorno.

## Ejecutar localmente (sin Render)
`pip install -r requirements.txt` y `uvicorn app:app --reload` (Windows: `iniciar_parkgo.bat`).
