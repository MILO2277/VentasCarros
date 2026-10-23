# Auto Cars

Aplicación web académica Flask para consultar vehículos, registrar usuarios, iniciar sesión, administrar carros y realizar compras simuladas. No procesa pagos reales.

La aplicación lee `.env` al iniciar. En este workspace está configurada con `REPOSITORY_BACKEND=firestore`; los usuarios, vehículos y compras se guardan en Cloud Firestore. Si se cambia a `REPOSITORY_BACKEND=memory`, se carga el catálogo de ejemplo en memoria y no se crean usuarios demo.

## Ejecutar en Windows

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Abre `http://127.0.0.1:5000`. El modo debug queda desactivado salvo que se habilite expresamente fuera de producción con `FLASK_DEBUG=true`.

## Operaciones iniciales en Firestore

```powershell
.\.venv\Scripts\python.exe -m flask --app run.py seed-cars
.\.venv\Scripts\python.exe -m flask --app run.py create-admin
```

`seed-cars` es idempotente: conserva documentos existentes, no borra, completa solo descripción/imagen si faltan y omite carros completos que coinciden por marca/modelo/año. En la carga inicial verificada añadió nueve vehículos y completó el Toyota `prueba-carro-001`; una segunda ejecución no modificó los diez documentos. `create-admin` pide el nombre, correo y contraseña en terminal; la contraseña se oculta, se confirma y se guarda con hash. No se crean cuentas de administrador al arrancar.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

La suite usa repositorios en memoria aislados y no cambia la base Firebase. Consulta [README_ARQUITECTURA.md](README_ARQUITECTURA.md) para capas, configuración, reglas y pruebas.

Las imágenes nuevas se guardan localmente en `flaskr/static/uploads/cars/`; Firestore almacena solo la ruta. Si se despliega en un servidor, ese directorio debe estar en almacenamiento persistente y tener copias de seguridad. Los archivos locales no se sincronizan automáticamente entre instancias y no deben borrarse al reconstruir o desplegar la aplicación.
