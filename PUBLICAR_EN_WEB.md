# Publicar Park Go desde GitHub en Render

**Park Go es una aplicación Python FastAPI, no un sitio estático.** Subir solamente `index.html` a Netlify o GitHub Pages **no hará funcionar el registro, las reservas ni el panel administrativo**. Debes publicar el servidor completo con almacenamiento persistente.

## Pasos

1. En [GitHub](https://github.com/), crea un repositorio nuevo llamado `park-go`. Preferiblemente **privado**.
2. Descomprime el ZIP y sube **los archivos de la carpeta `ParkGo_4_Profesional`** a la raíz del repositorio (no incluyas la carpeta contenedora; `app.py`, `requirements.txt`, `render.yaml` deben quedar arriba).
3. En [Render](https://dashboard.render.com/), inicia sesión, conecta GitHub y crea un nuevo **Blueprint** basado en ese repositorio. Render detectará `render.yaml`.
4. El Blueprint propone un Web Service Python con **disco persistente** en `/var/data`. Comprueba los precios: el disco requiere recursos de pago. Define en Render, nunca en GitHub:
   - `PARKGO_ADMIN_EMAIL`: tu correo administrativo.
   - `PARKGO_ADMIN_PASSWORD`: contraseña nueva de al menos 12 caracteres.
   - `SECRET_KEY`: Render puede generarla por ti.
5. Completa el despliegue y abre la dirección `https://<nombre>.onrender.com/` para el conductor y `https://<nombre>.onrender.com/business` para operador.
6. Crea una cuenta conductora desde la web, entra al panel con tus credenciales y comprueba una reserva. Si dejas el servicio en línea, revisa además políticas de privacidad, permisos de datos y medidas de seguridad antes de captar usuarios reales.

## Alternativa temporal para una exposición gratuita

Puedes configurar manualmente un Web Service Python **Free** en Render con:

```
Build Command: pip install -r requirements.txt
Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT
```

Variables de entorno: `PARKGO_ENV=production`, `SECRET_KEY` (cadena aleatoria de más de 32 caracteres), `PARKGO_ADMIN_EMAIL` y `PARKGO_ADMIN_PASSWORD`.

**Límite:** en el plan gratuito de Render no hay disco persistente para SQLite. La base de datos (cuentas, reservas y parqueaderos) puede borrarse tras un reinicio o un nuevo despliegue. Es apto solamente para un demo desechable. Para mostrarla con seguridad en la exposición, utiliza el disco persistente del Blueprint o ejecuta la versión local.

## Dónde cambiar el estilo y la lógica

- `static/ui.css` — diseño y responsividad.
- `static/driver.js` — vistas conductor, mapa, selección de plazas y comprobantes.
- `static/business.js` — panel web administrativo.
- `static/shared.js` — iconos y utilidades.
- `static/index.html` — entrada del conductor.
- `static/business.html` — entrada del administrador.
- `app.py` — API, cuentas, roles, transacciones y datos.
- `render.yaml` — configuración de publicación con disco persistente.

## Qué falta antes de clientes reales

Este proyecto es una **versión demostrable**, no una empresa en operación. No procesa pagos reales, no verifica correos electrónicos, y no incluye recuperación de contraseña ni reservas vinculadas a establecimientos verificados. Antes de abrirlo comercialmente deben añadirse controles de seguridad, respaldo de base de datos y cumplimiento legal correspondiente.
