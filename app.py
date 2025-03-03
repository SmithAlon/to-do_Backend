from flask import Flask, jsonify, request, abort
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson.json_util import dumps
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__)

# Configurar la conexión a MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/to-do-list"  # Cambia según tu configuración
mongo = PyMongo(app)

# Leer la clave secreta desde el archivo .env
API_KEY = os.getenv("API_KEY")

# Middleware para validar la clave API
def validar_api_key():
    clave_enviada = request.headers.get("X-API-KEY")
    if clave_enviada != API_KEY:
        abort(401, description="Clave API inválida")

# Aplicar el middleware a todas las rutas protegidas
@app.before_request
def antes_de_cada_solicitud():
    # Excluir rutas públicas si es necesario
    if request.endpoint not in ["public_route", "register", "login"]:
        validar_api_key()

# Endpoint público (opcional)
@app.route('/api/public', methods=['GET'])
def public_route():
    return jsonify({"mensaje": "Esta ruta es pública"})

# Ruta para registrar un nuevo usuario
@app.route('/api/register', methods=['POST'])
def register():
    username = request.json.get("username")
    password = request.json.get("password")
    if not username or not password:
        abort(400, description="Faltan datos")

    hashed_password = generate_password_hash(password)
    nuevo_usuario = {
        "username": username,
        "password": hashed_password
    }
    resultado = mongo.db.usuarios.insert_one(nuevo_usuario)
    return jsonify({"mensaje": "Usuario registrado", "id": str(resultado.inserted_id)}), 201

# Ruta para iniciar sesión
@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get("username")
    password = request.json.get("password")
    if not username or not password:
        abort(400, description="Faltan datos")

    usuario = mongo.db.usuarios.find_one({"username": username})
    if usuario and check_password_hash(usuario["password"], password):
        return jsonify({"mensaje": "Inicio de sesión exitoso"})
    abort(401, description="Credenciales inválidas")

# Ruta para obtener todas las tareas
@app.route('/api/tareas', methods=['GET'])
def get_tareas():
    tareas = mongo.db.tareas.find()
    return dumps(tareas)

# Ruta para obtener una tarea específica por ID
@app.route('/api/tareas/<id>', methods=['GET'])
def get_tarea(id):
    tarea = mongo.db.tareas.find_one({"_id": ObjectId(id)})
    if tarea:
        return dumps(tarea)
    abort(404, description="Tarea no encontrada")

# Ruta para crear una nueva tarea
@app.route('/api/tareas', methods=['POST'])
def create_tarea():
    nueva_tarea = {
        "titulo": request.json.get("titulo"),
        "descripcion": request.json.get("descripcion", ""),
        "completada": False
    }
    resultado = mongo.db.tareas.insert_one(nueva_tarea)
    return jsonify({"mensaje": "Tarea creada", "id": str(resultado.inserted_id)}), 201

# Ruta para actualizar una tarea existente
@app.route('/api/tareas/<id>', methods=['PUT'])
def update_tarea(id):
    tarea_actualizada = {
        "titulo": request.json.get("titulo"),
        "descripcion": request.json.get("descripcion"),
        "completada": request.json.get("completada")
    }
    resultado = mongo.db.tareas.update_one({"_id": ObjectId(id)}, {"$set": tarea_actualizada})
    if resultado.matched_count:
        return jsonify({"mensaje": "Tarea actualizada"})
    abort(404, description="Tarea no encontrada")

# Ruta para eliminar una tarea
@app.route('/api/tareas/<id>', methods=['DELETE'])
def delete_tarea(id):
    resultado = mongo.db.tareas.delete_one({"_id": ObjectId(id)})
    if resultado.deleted_count:
        return jsonify({"mensaje": "Tarea eliminada"})
    abort(404, description="Tarea no encontrada")

# Manejador de errores personalizado
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Acceso denegado", "mensaje": error.description}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Recurso no encontrado", "mensaje": error.description}), 404

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)