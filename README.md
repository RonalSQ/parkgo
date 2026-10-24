> **EDICIÓN ACADÉMICA PARA GITHUB + RENDER:** La base `parkgo.db` incluida solo contiene UN parqueadero de prueba y NINGÚN usuario ni reserva. En esta edición SÍ puedes subirla para facilitar la demostración. En Render Free los datos posteriores pueden perderse por reinicios o despliegues. Lee `PUBLICACION_DEMO.md` para el procedimiento exacto.

# Park Go 4.1 — Tu espacio, a un clic de distancia.

Una **aplicación web responsiva** para conductores y un **panel web para operadores** con el mismo servidor y base de datos. Proyecto académico (MVP), no servicio comercial.

## Cómo ejecutarlo en Windows

1. Descomprime el proyecto.
2. Usa **Python 3.11 a 3.15**. El iniciador prefiere Python 3.13/3.12 cuando están instalados y también admite 3.15. El script ya no requiere PyYAML ni compiladores de C++.
3. Haz doble clic en **`iniciar_parkgo.bat`**. La primera ejecución instalará las dependencias. Si la instalación anterior falló, puedes ejecutar el .bat nuevo en la misma carpeta sin borrar `parkgo.db`.
4. Abre **http://127.0.0.1:8000** para conductores.
5. Abre **http://127.0.0.1:8000/business** para operadores.
6. Para detener, cierra la ventana negra o presiona Ctrl+C.

## Contraseña del operador SOLO para el prototipo local

- Correo: `operador@parkgo-demo.com`
- Contraseña: `ParkGo2026!`

**NO publiques el proyecto con estas credenciales**. Configura `PARKGO_ADMIN_EMAIL`, `PARKGO_ADMIN_PASSWORD`, `SECRET_KEY` y `PARKGO_ENV=production` en el alojamiento antes de exponer la web a Internet. Para crear usuarios conductores, utiliza el botón **Ingresar > Registrarme gratis**.

## Funciones implementadas

### Conductor — `/`
- Diseño adaptativo para móvil, tablet y ordenador.
- Navegación por categorías **Auto** y **Moto**, tarjetas con imágenes, tarifas y mapa OpenStreetMap.
- Detalle del parqueadero con dirección, descripción, tarifas, capacidad y servicios.
- Registro e inicio de sesión con email/contraseña; sesiones con cookies HttpOnly.
- Selección por niveles con plazas **libres (verde)**, **ocupadas (gris)** y **seleccionadas (azul)**.
- Reserva con fecha, hora, duración y placa; cupos validados en transacción de base de datos.
- Comprobante QR privado, listado de reservas y cancelaciones.
- Las reservas coincidentes en el horario descuentan disponibilidad; se impide reservar dos veces la misma plaza.

### Park Go Business — `/business`
- Acceso independiente para administrador.
- Dashboard de cupos, parqueaderos y reservas.
- Crear, **editar** y **retirar** parqueaderos. Retirar los archiva para preservar históricos; se pueden restaurar.
- Tarifas, horarios, ubicación, servicios, fotografías ilustrativas y distribución por niveles independientes.
- Registrar ingreso y salida de vehículos, verificar códigos de reserva.

## Datos demo

El sistema inicia con **un solo parqueadero ficticio**, "Park Go Central", en Pamplona. Sus precios, ubicación y servicios son **simulados**. Puedes editarlo o retirarlo desde Business. Si deseas empezar desde cero, detén el servidor y elimina el archivo `parkgo.db` (se perderán usuarios y reservas de pruebas). Al iniciar nuevamente se generará el parqueadero demo.

Las fotografías son ilustrativas. El mapa usa una librería/teselas externas y necesita internet.

## Publicar en la web — GitHub + Render

### Opción recomendada: datos persistentes (requiere alojamiento compatible con disco, posiblemente de pago)

1. Crea un repositorio en GitHub **preferiblemente privado** y sube los archivos de esta carpeta a su raíz. No subas `parkgo.db`, `.venv` ni archivos `.env`.
2. En Render, crea un servicio desde ese repositorio, o selecciona el **Blueprint** definido en `render.yaml`.
3. El archivo `render.yaml` establece Python, comando de inicio y una carpeta `/var/data` para un disco persistente. Confirma los precios vigentes antes de contratar.
4. Define un correo y una contraseña nuevos para el operador, distintos de los de prueba; elige una contraseña larga y única.
5. Despliega. La dirección será del tipo `https://<tu-servicio>.onrender.com`.
6. Los usuarios entrarán por `/` y el administrador por `/business`; **ambos se conectan a la misma base de datos**.

### Opción gratuita temporal (solo exposición)

Puede desplegarse como **Web Service Free** en Render siguiendo los comandos: 

- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Env: `PARKGO_ENV=production`, `SECRET_KEY` (aleatoria larga), `PARKGO_ADMIN_EMAIL`, `PARKGO_ADMIN_PASSWORD`.

**Advertencia crucial:** sin almacenamiento persistente, la base SQLite se perderá al reiniciar o redesplegar la instancia. Las reservas y cuentas NO serán confiables. Este modo sirve únicamente como demostración desechable. Para persistir datos se necesita disco persistente o modificar el proyecto para usar una base externa como PostgreSQL.

Render despliega FastAPI desde GitHub: https://render.com/docs/deploy-fastapi

## Arquitectura

- **Backend:** FastAPI en Python.
- **Persistencia:** SQLite con transacciones `BEGIN IMMEDIATE` y restricciones de integridad. Un solo proceso de servidor.
- **Autenticación:** Contraseñas PBKDF2 SHA-256 con salt, cookie firmada HttpOnly, expiración de 24 horas, autorización por rol y token CSRF en operaciones autenticadas.
- **Frontend:** HTML, CSS responsivo, JavaScript sin compilación ni Node.js.
- **Mapa:** Leaflet + teselas de OpenStreetMap (requiere internet).
- **QR:** Generación desde el servidor, accesible solamente al titular o administrador.

## Pruebas

Con `pytest` disponible, ejecutar:

```bash
python -m pytest -q tests
```

Pruebas automatizadas cubren autenticación/autorización, plazas duplicadas, descuento y liberación de cupos, alta/edición/archivo/restauración y protección de reserva/QR.

## Pendientes para un servicio real

- Verificación de correo, recuperación de contraseñas, protección contra abuso e inicio de sesión con proveedor externo.
- Política de datos personales, consentimiento y gestión legal de establecimientos.
- Pasarela de pagos y conciliación de cobros (hoy **pago presencial**, no pagos integrados).
- Fotografías, calificaciones y disponibilidad verificadas de establecimientos reales.
- Confirmar GPS/direcciones, permisos y acuerdos con parqueaderos, auditoría y monitoreo de producción.
- Las plazas representan una **cuadrícula configurable**; no son planos arquitectónicos ni sensores reales.

No describir esta entrega como plataforma comercial desplegada/validada: es un **prototipo funcional académico con base para continuar el desarrollo**.

## Corrección 4.1 — Fallo de PyYAML con Python 3.15

El paquete `uvicorn[standard]` instalaba PyYAML, que intentaba compilarse en Windows y solicitaba MSVC. El servidor no usa características de esa dependencia. Cambiamos a `uvicorn` básico y mejoramos la detección de Python. Si tienes la carpeta de la versión 4.0 con datos que deseas conservar, copia los dos archivos de `ParkGo_4_1_PARCHE_iniciar_y_dependencias.zip` dentro de la carpeta `ParkGo`, aceptando reemplazar. Tus cuentas y reservas permanecen en `parkgo.db`. Si vuelve a fallar, elimina solamente `.venv` y vuelve a ejecutar el iniciador.

## Arranque Windows 4.3
Lee LEEME_PRIMERO_WINDOWS.md. Ya no se exige 3.13.
