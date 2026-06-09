"""
test_connection.py
Verifica que la conexión a MongoDB Atlas funciona correctamente.
Ejecutar ANTES de cualquier otro script.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")


def test_conexion():
    """
    Verifica la conexión completa a MongoDB Atlas.
    Prueba ping, permisos de escritura y lectura.
    """
    cliente = MongoClient(MONGO_URI)
    
    # Verificar autenticación y red
    cliente.admin.command('ping')
    
    # Verificar permisos de escritura/lectura
    db = cliente["test_verificacion"]
    resultado = db.test.insert_one({"test": True})
    db.test.delete_one({"_id": resultado.inserted_id})
    
    print("✅ Conexión exitosa")
    cliente.close()


if __name__ == "__main__":
    test_conexion()