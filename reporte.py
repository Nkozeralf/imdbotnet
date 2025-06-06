import os
import logging
from datetime import datetime
from collections import defaultdict

LOG_FILE = "logs/pedidos.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("reporte")

def analizar_logs(log_path: str = LOG_FILE) -> dict:
    if not os.path.exists(log_path):
        logger.error("No se encontró el archivo de log: %s", log_path)
        return {}

    resultados = {
        "total": 0,
        "exitosos": 0,
        "fallidos": 0,
        "tiendas": defaultdict(int),
        "ciudades": defaultdict(int),
        "ips": set(),
        "tiempo_inicio": None,
        "tiempo_fin": None
    }

    with open(log_path, "r", encoding="utf-8") as f:
        for linea in f:
            resultados["total"] += 1

            partes = linea.strip().split(" | ")
            if len(partes) < 5:
                continue

            timestamp_str, tienda, pedido, cliente, ciudad = partes[:5]

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                if not resultados["tiempo_inicio"] or timestamp < resultados["tiempo_inicio"]:
                    resultados["tiempo_inicio"] = timestamp
                if not resultados["tiempo_fin"] or timestamp > resultados["tiempo_fin"]:
                    resultados["tiempo_fin"] = timestamp
            except:
                continue

            if pedido.startswith("Pedido #"):
                resultados["exitosos"] += 1
            else:
                resultados["fallidos"] += 1

            resultados["tiendas"][tienda.strip()] += 1
            resultados["ciudades"][ciudad.strip().upper()] += 1

    return resultados

def imprimir_reporte(datos: dict):
    if not datos:
        logger.warning("No hay datos para mostrar.")
        return

    print("\n==============================")
    print("     REPORTE DE PEDIDOS     ")
    print("==============================")
    print(f"Total de pedidos:        {datos['total']}")
    print(f"Pedidos exitosos:        {datos['exitosos']}")
    print(f"Pedidos fallidos:        {datos['fallidos']}")

    if datos['total'] > 0:
        exito_pct = (datos['exitosos'] / datos['total']) * 100
        print(f"Porcentaje de éxito:     {exito_pct:.2f}%")

    if datos['tiempo_inicio'] and datos['tiempo_fin']:
        duracion = datos['tiempo_fin'] - datos['tiempo_inicio']
        print(f"Duración total:          {duracion}")

    print("\nPedidos por tienda:")
    for tienda, cantidad in datos['tiendas'].items():
        print(f"  - {tienda}: {cantidad}")

    print("\nPedidos por ciudad:")
    for ciudad, cantidad in datos['ciudades'].items():
        print(f"  - {ciudad}: {cantidad}")

if __name__ == "__main__":
    resultados = analizar_logs()
    imprimir_reporte(resultados)