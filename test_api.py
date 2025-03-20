import requests

# URL de tu API
BASE_URL = "http://localhost:5000/api"

# Headers con la API Key
headers = {
    "X-API-KEY": "mi_clave_secreta_12345",
    "Content-Type": "application/json"
}

# Ejemplo: Obtener todas las tareas
response = requests.get(f"{BASE_URL}/tareas", headers=headers)
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

# Ejemplo: Crear una nueva tarea
nueva_tarea = {
    "titulo": "Completar proyecto",
    "descripcion": "Terminar el proyecto de Python"
}
response = requests.post(f"{BASE_URL}/tareas", headers=headers, json=nueva_tarea)
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")