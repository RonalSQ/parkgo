# Mejoras de la demostración

- Diseño del logo del equipo adaptado en horizontal, con fondo transparente, símbolo a la izquierda y ParkGo a la derecha. Negro y amarillo sobre fondos claros; versión monocromática blanca sobre fondos oscuros.
- Mapa con URL y política de referencia compatibles con OpenStreetMap, atribución visible y aviso de error de conexión.
- Registro de parqueaderos mediante dirección escrita y punto seleccionado en el mapa. El punto puede elegirse con un clic, arrastrando el marcador, usando el centro del mapa o la ubicación del dispositivo. Es necesario confirmar una ubicación antes de guardar. La dirección no se convierte automáticamente en coordenadas.
- Fecha y hora de Colombia visibles antes del plano de espacios.
- Disponibilidad sin caché, actualización cada 15 segundos mientras el plano está visible y protección frente a respuestas atrasadas al cambiar el horario.
- Confirmación deshabilitada durante consultas o envíos. La base de datos valida nuevamente la disponibilidad dentro de una transacción.
- Botones más grandes, textos con mayor contraste, iconos en la navegación móvil y controles de teclado en los diálogos.

## Comprobación para la exposición

1. Inicia la app con `iniciar_parkgo.bat` y abre `http://127.0.0.1:8000`.
2. Crea una cuenta de conductor y reserva A-06 para mañana de 10:00 a 12:00.
3. Vuelve al mismo parqueadero y horario: A-06 debe aparecer ocupado.
4. Cambia a las 12:00: puede aparecer libre porque esa reserva ya terminó.
5. Cancela la reserva desde Mis reservas: el espacio se libera para ese horario.
6. Desde el panel del operador, agrega un parqueadero y marca su entrada en el mapa.

Las pruebas automáticas incluyen reservas simultáneas, cruces de horario, cancelación, permisos y registro de establecimientos. Ejecuta `.venv/Scripts/python.exe -m pytest -q` tras instalar `pytest` y `httpx` en el entorno virtual.

Los mapas necesitan internet y dependen de la disponibilidad de OpenStreetMap. Esta app sigue siendo una demostración: no procesa pagos reales. Los cambios locales deben publicarse para que aparezcan en el enlace de Render.


## Acceso y parqueadero Hermanos G (25 de octubre de 2026)

- El formulario incluye Conductor / Administrador también en celular. Las cuentas administradoras se redirigen a /business; las cuentas de conductor no pueden gestionar parqueaderos.
- Cuenta adicional de demostración: admin@admin.com / admin1234. Gestiona Park Go Central; no usar estas credenciales públicas para datos reales.
- Hermanos G: Carrera 8 # 1A-41, Pamplona, con la foto aportada. Datos simulados: 24 autos, 12 motos, $4.000/h auto, $2.000/h moto, 06:00–22:00. Coordenadas aproximadas editables desde el panel.
- Las incorporaciones se crean al iniciar el servidor, incluso en bases existentes; no duplican registros ni sobrescriben ediciones o archivos del parqueadero en reinicios.


## Separación por propietario

- Park Go Central: admin@admin.com / admin1234.
- Hermanos G: hermanosg@admin.com / hermanos123.
- Cada cuenta administra únicamente sus parqueaderos, reservas, métricas y códigos QR. Los conductores siguen viendo el catálogo completo.
- Cada nueva sede se asigna automáticamente al administrador que la crea. La API no permite elegir ni modificar el propietario mediante el formulario.
- La migración conserva las reservas existentes y las asignaciones en reinicios. Otros establecimientos antiguos se asignan al operador configurado en PARKGO_ADMIN_EMAIL. Esa cuenta tampoco tiene acceso global.
