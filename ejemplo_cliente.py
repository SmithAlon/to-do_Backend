import requests
import json

# URL base de la API
BASE_URL = "http://localhost:5000/api"

# Headers para las solicitudes
headers = {
    "X-API-KEY": "mi_clave_secreta_12345",
    "Content-Type": "application/json"
}

def mostrar_respuesta(response):
    """Muestra la respuesta de la API de forma legible"""
    print(f"Status code: {response.status_code}")
    try:
        print(f"Respuesta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Respuesta: {response.text}")
    print("-" * 50)

def registrar_usuario(username, password):
    """Registra un nuevo usuario"""
    datos = {
        "username": username,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/register", headers=headers, json=datos)
    print("Registro de usuario:")
    mostrar_respuesta(response)
    return response.json() if response.status_code == 201 else None

def iniciar_sesion(username, password):
    """Inicia sesión y obtiene un token JWT"""
    datos = {
        "username": username,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/login", headers=headers, json=datos)
    print("Inicio de sesión:")
    mostrar_respuesta(response)
    
    if response.status_code == 200:
        return response.json().get("token")
    return None

def obtener_tareas(token):
    """Obtiene todas las tareas del usuario"""
    auth_headers = headers.copy()
    auth_headers["Authorization"] = f"Bearer {token}"
    
    response = requests.get(f"{BASE_URL}/tareas", headers=auth_headers)
    print("Tareas del usuario:")
    mostrar_respuesta(response)
    return response.json() if response.status_code == 200 else []

def crear_tarea(token, titulo, descripcion=""):
    """Crea una nueva tarea"""
    auth_headers = headers.copy()
    auth_headers["Authorization"] = f"Bearer {token}"
    
    datos = {
        "titulo": titulo,
        "descripcion": descripcion
    }
    
    response = requests.post(f"{BASE_URL}/tareas", headers=auth_headers, json=datos)
    print(f"Crear tarea '{titulo}':")
    mostrar_respuesta(response)
    return response.json() if response.status_code == 201 else None

def actualizar_tarea(token, tarea_id, datos):
    """Actualiza una tarea existente"""
    auth_headers = headers.copy()
    auth_headers["Authorization"] = f"Bearer {token}"
    
    response = requests.put(f"{BASE_URL}/tareas/{tarea_id}", headers=auth_headers, json=datos)
    print(f"Actualizar tarea {tarea_id}:")
    mostrar_respuesta(response)
    return response.status_code == 200

def eliminar_tarea(token, tarea_id):
    """Elimina una tarea"""
    auth_headers = headers.copy()
    auth_headers["Authorization"] = f"Bearer {token}"
    
    response = requests.delete(f"{BASE_URL}/tareas/{tarea_id}", headers=auth_headers)
    print(f"Eliminar tarea {tarea_id}:")
    mostrar_respuesta(response)
    return response.status_code == 200

def ejemplo_completo():
    """Ejecuta un ejemplo completo del flujo de la aplicación"""
    # Registrar un usuario
    registrar_usuario("usuario_ejemplo", "contraseña123")
    
    # Iniciar sesión
    token = iniciar_sesion("usuario_ejemplo", "contraseña123")
    if not token:
        print("No se pudo iniciar sesión")
        return
    
    # Crear varias tareas
    crear_tarea(token, "Hacer compras", "Comprar frutas y verduras")
    crear_tarea(token, "Estudiar Python", "Repasar Flask y MongoDB")
    crear_tarea(token, "Hacer ejercicio", "30 minutos de cardio")
    
    # Obtener todas las tareas
    tareas = obtener_tareas(token)
    
    if tareas and len(tareas) > 0:
        # Tomar la primera tarea para actualizar
        primera_tarea_id = tareas[0]["_id"]
        
        # Actualizar la tarea
        actualizar_tarea(token, primera_tarea_id, {
            "titulo": "Hacer compras - URGENTE",
            "completada": True
        })
        
        # Eliminar la última tarea
        ultima_tarea_id = tareas[-1]["_id"]
        eliminar_tarea(token, ultima_tarea_id)
    
    # Verificar las tareas después de las operaciones
    obtener_tareas(token)

if __name__ == "__main__":
    ejemplo_completo() 