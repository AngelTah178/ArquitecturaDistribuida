/**
 * Universidad Politécnica de Quintana Roo - Proyecto Final Integrador
 * Script de Provisión de Seguridad y Roles para MongoDB Atlas
 * 
 * Roles requeridos:
 *  - mongo_developer (readWrite, dbAdmin, userAdmin)
 *  - mongo_user (readWrite)
 * 
 * Usuarios requeridos:
 *  - developer1
 *  - user1
 */

const DB_NAME = "upqroo_distribuida";
db = db.getSiblingDB(DB_NAME);

print(`--- Configurando roles y usuarios en base de datos: ${DB_NAME} ---`);

// 1. Crear rol personalizado: mongo_developer
try {
  db.createRole({
    role: "mongo_developer",
    privileges: [
      {
        resource: { db: DB_NAME, collection: "" },
        actions: [
          "find", "insert", "remove", "update",
          "createCollection", "dropCollection", "createIndex", "dropIndex",
          "collMod", "compact", "collStats", "dbStats"
        ]
      }
    ],
    roles: [
      { role: "readWrite", db: DB_NAME },
      { role: "dbAdmin", db: DB_NAME },
      { role: "userAdmin", db: DB_NAME }
    ]
  });
  print("Rol 'mongo_developer' creado exitosamente.");
} catch (e) {
  print("Rol 'mongo_developer' ya existe o mensaje: " + e.message);
}

// 2. Crear rol personalizado: mongo_user
try {
  db.createRole({
    role: "mongo_user",
    privileges: [
      {
        resource: { db: DB_NAME, collection: "" },
        actions: ["find", "insert", "remove", "update"]
      }
    ],
    roles: [
      { role: "readWrite", db: DB_NAME }
    ]
  });
  print("Rol 'mongo_user' creado exitosamente.");
} catch (e) {
  print("Rol 'mongo_user' ya existe o mensaje: " + e.message);
}

// 3. Crear usuario: developer1
try {
  db.createUser({
    user: "developer1",
    pwd: "developerPassword2026!",
    roles: [
      { role: "mongo_developer", db: DB_NAME }
    ]
  });
  print("Usuario 'developer1' creado exitosamente con rol 'mongo_developer'.");
} catch (e) {
  print("Usuario 'developer1' ya existe o mensaje: " + e.message);
}

// 4. Crear usuario: user1
try {
  db.createUser({
    user: "user1",
    pwd: "userPassword2026!",
    roles: [
      { role: "mongo_user", db: DB_NAME }
    ]
  });
  print("Usuario 'user1' creado exitosamente con rol 'mongo_user'.");
} catch (e) {
  print("Usuario 'user1' ya existe o mensaje: " + e.message);
}

// 5. Creación e indexación de las 2 colecciones requeridas
print("--- Inicializando colecciones e índices de MongoDB ---");

// Colección 1: pedidos
if (!db.getCollectionNames().includes("pedidos")) {
  db.createCollection("pedidos");
}
db.pedidos.createIndex({ "fecha": 1 });
db.pedidos.createIndex({ "sync_status": 1 });
db.pedidos.createIndex({ "updated_at": 1 });
db.pedidos.createIndex({ "cliente.correo": 1 });

// Colección 2: auditoria_operaciones
if (!db.getCollectionNames().includes("auditoria_operaciones")) {
  db.createCollection("auditoria_operaciones");
}
db.auditoria_operaciones.createIndex({ "timestamp": -1 });
db.auditoria_operaciones.createIndex({ "cluster_id": 1 });
db.auditoria_operaciones.createIndex({ "usuario_id": 1 });

print("--- Inicialización de MongoDB completada exitosamente ---");
