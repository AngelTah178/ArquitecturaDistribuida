# 🌐 Arquitectura Distribuida y Sincronizada (MongoDB Atlas & PostgreSQL Neon)
**Universidad Politécnica de Quintana Roo (UPQROO)**  
*Ingeniería en Tecnologías de la Información e Innovación Digital*  
*Asignatura: Bases de Datos en la Nube (7° Cuatrimestre) — Proyecto Final Integrador*

---

## 📌 1. Descripción del Proyecto
Este proyecto implementa una solución computacional distribuida y resiliente basada en servicios cloud que integra:
- **Base de Datos NoSQL**: 3 Clusters de **MongoDB Atlas** con enrutamiento y balanceo de carga dinámico según la concurrencia de usuarios.
- **Base de Datos Relacional**: **PostgreSQL en Neon Cloud** con un modelo de datos normalizado (3FN) de 5 tablas.
- **Servicio ETL Automatizado**: Extracción de cambios desde MongoDB, transformación NoSQL $\rightarrow$ Relacional y carga consistente en PostgreSQL cada **3 minutos** mediante `APScheduler`.
- **API REST**: Desarrollada en **FastAPI** (Python 3.12) con Swagger interactivo (`/docs`), endpoints de Catálogos (CRUD), Consultas y Monitoreo.
- **Dashboard Web en Tiempo Real**: Visualización interactiva con animación del flujo de datos, semáforo de sincronización, tarjetas de métricas y control de bots concurrentes.

---

## 🏗️ 2. Arquitectura del Sistema en Capas

```text
                                 [ BOTS SIMULADOS ]
                               (1 a 9 Usuarios Activos)
                                         │
                                         ▼ (HTTP REST CRUD)
                     ┌───────────────────────────────────────┐
                     │          API REST / FASTAPI           │
                     │     Enrutador Dinámico de Carga       │
                     └───────────────────┬───────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              ▼ (1 - 3 usuarios)         ▼ (4 - 6 usuarios)         ▼ (7 - 9 usuarios)
     ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
     │ Cluster Mongo #1 │       │ Cluster Mongo #2 │       │ Cluster Mongo #3 │
     └────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
              │                          │                          │
              └──────────────────────────┼──────────────────────────┘
                                         │
                                         ▼ (Lectura Diferencial)
                             ┌───────────────────────┐
                             │    SERVICIO ETL       │ (Cada 3 minutos con APScheduler)
                             │ Extract-Transform-Load│ Control de Duplicados & Trazabilidad
                             └───────────┬───────────┘
                                         │
                                         ▼ (Persistir Datos 3FN)
                             ┌───────────────────────┐
                             │   POSTGRESQL (NEON)   │
                             │ 5 Tablas Normalizadas │
                             └───────────────────────┘
```

---

## ⚖️ 3. Regla de Escalamiento y Enrutamiento Dinámico
El sistema detecta automáticamente la cantidad de usuarios/bots activos y redirige las operaciones de escritura y lectura al cluster de MongoDB asignado:

| Usuarios Activos | Cluster de MongoDB Utilizado | Capacidad / Nivel de Carga |
| :---: | :---: | :---: |
| **1 a 3** | `Cluster Mongo #1` | Carga Baja |
| **4 a 6** | `Cluster Mongo #2` | Carga Media |
| **7 a 9** | `Cluster Mongo #3` | Carga Alta |

---

## 🗄️ 4. Modelo de Datos y Seguridad (Roles y Usuarios)

### MongoDB Atlas (NoSQL)
- **Colecciones (2)**:
  1. `pedidos`: Contiene los pedidos con cliente embebido y arreglo de productos.
  2. `auditoria_operaciones`: Bitácora histórica de transacciones CRUD por cluster.
- **Roles y Usuarios**:
  - `mongo_developer` (`readWrite`, `dbAdmin`, `userAdmin`) $\rightarrow$ Usuario: `developer1`
  - `mongo_user` (`readWrite`) $\rightarrow$ Usuario: `user1`
  - *Script de provisión:* `backend/scripts/init_mongo_users.js`

### PostgreSQL Neon (Relacional 3FN)
- **Tablas Normalizadas (5)**:
  1. `clientes`: (`cliente_id` PK, `nombre`, `correo` UNIQUE, `telefono`, `creado_en`)
  2. `productos`: (`producto_id` PK, `sku` UNIQUE, `nombre`, `precio`, `stock`, `creado_en`)
  3. `pedidos`: (`pedido_id` PK, `cliente_id` FK, `fecha`, `mongo_id` UNIQUE, `cluster_origen`, `total`, `sincronizado_en`)
  4. `detalle_pedido`: (`detalle_id` PK, `pedido_id` FK, `producto_id` FK, `cantidad`, `precio_unitario`, `subtotal`)
  5. `sync_logs`: (`sync_id` PK, `fecha_ejecucion`, `cluster_origen`, `registros_extraidos`, `registros_cargados`, `estado`, `tiempo_ms`, `mensaje`)
- **Roles y Usuarios**:
  - `postgres_developer` (Login, Connect, Create, Usage, CRUD, Alter Default Privileges) $\rightarrow$ Usuario: `dev1`
  - `postgres_user` (Login, CRUD, Uso de vistas y funciones) $\rightarrow$ Usuario: `usr1`
  - *Script de provisión:* `backend/scripts/init_postgres_schema.sql`

---

## 🔄 5. Servicio ETL y Transformación (Capa 4)
- **Extraer**: Filtra documentos con `sync_status = 'PENDING'` en los 3 clusters de MongoDB.
- **Transformar**:
  ```json
  // Entrada NoSQL (MongoDB):
  {
    "_id": "673b0001...",
    "cliente": { "nombre": "Juan Perez", "correo": "juan@mail.com" },
    "productos": [{ "id": 1, "cantidad": 2, "precio": 450.0 }],
    "fecha": "2026-10-01"
  }
  ```
  Se desanida y normaliza en:
  - Registro en `clientes` (evitando duplicados mediante upsert por correo).
  - Registro maestro en `pedidos` (vinculado a `cliente_id` y `mongo_id`).
  - N registros en `detalle_pedido` (vinculados al pedido y al catálogo de `productos`).
- **Cargar**: Transacción atómica en PostgreSQL Neon.
- **Trazabilidad**: Actualiza en MongoDB `sync_status = 'SYNCED'` y `synced_at`, y genera registro en `sync_logs`.
- **Frecuencia**: Se ejecuta automáticamente cada **3 minutos** mediante `APScheduler`.

---

## 📡 6. Catálogo de Endpoints de la API REST

### Catálogos (CRUD)
- `POST /api/v1/pedidos`: Crea un pedido en MongoDB enrutado dinámicamente al cluster según usuarios activos.
- `GET /api/v1/pedidos`: Lista pedidos con opción de filtrar por cluster (`?cluster_id=1`).
- `GET /api/v1/pedidos/{id}`: Consulta detalle de un pedido por su identificador.
- `PUT /api/v1/pedidos/{id}`: Modifica un pedido y lo marca como pendiente para el ETL.
- `DELETE /api/v1/pedidos/{id}`: Elimina un pedido de su cluster.

### Consultas
- `GET /estadisticas`: Resumen general de volumen de datos y operaciones.
- `GET /sincronizacion`: Estado del último proceso ETL, acumulados y tiempos.
- `POST /sincronizacion/trigger`: Dispara manualmente una sincronización ETL inmediata.
- `GET /health`: Health check de los 3 Clusters Mongo y PostgreSQL Neon.

### Monitoreo
- `GET /clusters`: Lista los clusters, reglas de enrutamiento y latencias.
- `GET /usuarios`: Muestra la lista y conteo de usuarios y bots activos concurrentes.
- `GET /metrics`: Métricas para tarjetas de monitoreo.

### Simulador de Bots
- `GET /api/v1/bots/status`: Estado y operación actual de cada uno de los 9 bots.
- `POST /api/v1/bots/control?count={N}`: Inicia o ajusta N bots concurrentes (0 a 9).
- `POST /api/v1/bots/stop`: Detiene todos los bots.

---

## 🚀 7. Instrucciones de Instalación y Ejecución

### Prerrequisitos
- Python 3.12+ instalado.
- Opcional: Cuentas de MongoDB Atlas y Neon Cloud (el sistema cuenta con modo simulado resiliente integrado para pruebas sin conexión).

### 1. Clonar el Repositorio y Configurar Entorno
```bash
cd backend
# Activar entorno virtual
.venv\Scripts\activate
# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno (`.env`)
Copiar el archivo de ejemplo:
```bash
cp .env.example .env
```
Configurar las URIs de los 3 clusters de MongoDB Atlas y Neon PostgreSQL en `.env`.

### 3. Ejecutar las Pruebas Automatizadas
```bash
$env:PYTHONPATH="backend"
.venv\Scripts\pytest -v tests/
```

### 4. Iniciar el Servidor FastAPI
```bash
python main.py
# o con uvicorn:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Acceso a las Interfaces
- **Dashboard de Simulación**: Abre tu navegador en `http://localhost:8000/dashboard` o `http://localhost:8000/`.
- **Documentación Swagger OpenAPI**: Accede a `http://localhost:8000/docs`.
