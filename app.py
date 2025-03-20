from flask import Flask, jsonify, request, abort
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from bson.json_util import dumps
from dotenv import load_dotenv
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS  # Importar CORS
import jwt
from datetime import datetime, timedelta
from functools import wraps

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__)

# Configurar CORS para permitir solicitudes desde cualquier origen
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configurar la conexión a MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/to-do-list"  # Cambia según tu configuración
mongo = PyMongo(app)

# Leer la clave secreta desde el archivo .env
API_KEY = os.getenv("API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "clave_secreta_para_jwt")

# Middleware para validar la clave API
def validar_api_key():
    clave_enviada = request.headers.get("X-API-KEY")
    if clave_enviada != API_KEY:
        abort(401, description="Clave API inválida")

# Decorator para verificar JWT token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            abort(401, description="Token no proporcionado")
        
        try:
            # Quitar 'Bearer ' si está presente
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            current_user = mongo.db.usuarios.find_one({"_id": ObjectId(data['user_id'])})
            if not current_user:
                abort(401, description="Usuario no válido")
        except:
            abort(401, description="Token inválido")
            
        return f(current_user, *args, **kwargs)
    
    return decorated

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

    # Verificar si el usuario ya existe
    usuario_existente = mongo.db.usuarios.find_one({"username": username})
    if usuario_existente:
        abort(400, description="El nombre de usuario ya existe")

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
        # Crear token JWT
        token = jwt.encode({
            'user_id': str(usuario['_id']),
            'username': usuario['username'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET)
        
        return jsonify({
            "mensaje": "Inicio de sesión exitoso",
            "token": token,
            "username": usuario['username']
        })
    abort(401, description="Credenciales inválidas")

# Ruta para obtener todas las tareas del usuario actual
@app.route('/api/tareas', methods=['GET'])
@token_required
def get_tareas(current_user):
    tareas = mongo.db.tareas.find({"user_id": str(current_user['_id'])})
    return dumps(tareas)

# Ruta para obtener una tarea específica por ID
@app.route('/api/tareas/<id>', methods=['GET'])
@token_required
def get_tarea(current_user, id):
    tarea = mongo.db.tareas.find_one({"_id": ObjectId(id), "user_id": str(current_user['_id'])})
    if tarea:
        return dumps(tarea)
    abort(404, description="Tarea no encontrada")

# Ruta para crear una nueva tarea
@app.route('/api/tareas', methods=['POST'])
@token_required
def create_tarea(current_user):
    titulo = request.json.get("titulo")
    if not titulo:
        abort(400, description="El título es obligatorio")
        
    nueva_tarea = {
        "titulo": titulo,
        "descripcion": request.json.get("descripcion", ""),
        "completada": False,
        "user_id": str(current_user['_id']),
        "fecha_creacion": datetime.utcnow()
    }
    resultado = mongo.db.tareas.insert_one(nueva_tarea)
    return jsonify({"mensaje": "Tarea creada", "id": str(resultado.inserted_id)}), 201

# Ruta para actualizar una tarea existente
@app.route('/api/tareas/<id>', methods=['PUT'])
@token_required
def update_tarea(current_user, id):
    # Verificar que la tarea pertenece al usuario
    tarea = mongo.db.tareas.find_one({"_id": ObjectId(id), "user_id": str(current_user['_id'])})
    if not tarea:
        abort(404, description="Tarea no encontrada")
    
    # Campos a actualizar
    actualizacion = {}
    if "titulo" in request.json:
        actualizacion["titulo"] = request.json.get("titulo")
    if "descripcion" in request.json:
        actualizacion["descripcion"] = request.json.get("descripcion")
    if "completada" in request.json:
        actualizacion["completada"] = request.json.get("completada")
    
    actualizacion["fecha_modificacion"] = datetime.utcnow()
    
    resultado = mongo.db.tareas.update_one(
        {"_id": ObjectId(id), "user_id": str(current_user['_id'])}, 
        {"$set": actualizacion}
    )
    
    return jsonify({"mensaje": "Tarea actualizada"})

# Ruta para eliminar una tarea
@app.route('/api/tareas/<id>', methods=['DELETE'])
@token_required
def delete_tarea(current_user, id):
    resultado = mongo.db.tareas.delete_one({"_id": ObjectId(id), "user_id": str(current_user['_id'])})
    if resultado.deleted_count:
        return jsonify({"mensaje": "Tarea eliminada"})
    abort(404, description="Tarea no encontrada")

# Manejador de errores personalizado
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Solicitud incorrecta", "mensaje": error.description}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Acceso denegado", "mensaje": error.description}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Recurso no encontrado", "mensaje": error.description}), 404

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

    