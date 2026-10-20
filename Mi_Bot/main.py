from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI(
    title="Broker AI Enterprise API",
    description="API privada de arbitraje para agentes autónomos.",
    version="1.0.0"
)

# Inicializar base de datos local para el servidor en la nube
def obtener_conexion_bd():
    conn = sqlite3.connect('broker_real.db')
    conn.row_factory = sqlite3.Row
    return conn

# Configuración inicial de la tabla si no existe
def inicializar_bd():
    conn = obtener_conexion_bd()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario_proveedor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT,
            precio_costo INTEGER
        )
    ''')
    # Insertar un producto de prueba si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM inventario_proveedor")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO inventario_proveedor (producto, precio_costo) VALUES ('Sistema_ERP', 20)")
        conn.commit()
    conn.close()

inicializar_bd()

class PeticionCompra(BaseModel):
    api_key_cliente: str
    producto_solicitado: str
    oferta_bitcoins: int

@app.post("/api/v1/comprar")
def solicitar_compra(peticion: PeticionCompra):
    # Validar llave de API secreta
    if peticion.api_key_cliente != "KEY_CLIENTE_AUTORIZADO_123":
        raise HTTPException(status_code=401, detail="🔒 Llave de API no válida o no autorizada.")
    
    conn = obtener_conexion_bd()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, precio_costo FROM inventario_proveedor WHERE producto = ? ORDER BY precio_costo ASC LIMIT 1",
        (peticion.producto_solicitado,)
    )
    proveedor = cursor.fetchone()
    
    if not proveedor:
        conn.close()
        raise HTTPException(status_code=444, detail="Producto no disponible en este momento.")
    
    precio_costo = proveedor['precio_costo']
    
    if peticion.oferta_bitcoins >= precio_costo:
        ganancia_neta = peticion.oferta_bitcoins - precio_costo
        
        cursor.execute("DELETE FROM inventario_proveedor WHERE id = ?", (proveedor['id'],))
        conn.commit()
        conn.close()
        
        return {
            "estado": "TRANSACCIÓN_EXITOSA",
            "mensaje": f"Has adquirido '{peticion.producto_solicitado}' exitosamente.",
            "monto_pagado_btc": peticion.oferta_bitcoins,
            "detalles_proveedor": "OCULTO_POR_POLITICA_DE_CONFIDENCIALIDAD",
            "log_interno_broker": {
                "ganancia_limpia_retenida_btc": ganancia_neta
            }
        }
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Oferta insuficiente para completar la transacción.")