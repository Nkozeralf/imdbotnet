# limpiador_logs.py

import os
import shutil
import logging

# Configuración de logging para limpieza
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("limpiador_logs")

def limpiar_logs(confirmado: bool = False):
    """
    Elimina logs, capturas y subdirectorios bajo 'logs/'.
    """
    rutas_a_limpiar = [
        "logs/automation.log",
        "logs/error_critico.html",
        "logs/ultima_respuesta.html",
    ]
    carpetas_logs = ["logs"]

    if not confirmado:
        resp = input("\n¿Deseas borrar los logs, capturas y registros anteriores? (s/n): ").lower()
        if resp != "s":
            logger.info("Operación cancelada por el usuario.")
            return

    # Eliminar archivos individuales
    for ruta in rutas_a_limpiar:
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
                logger.info(f"Archivo eliminado: {ruta}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar {ruta}: {e}")

    # Eliminar todos los archivos y subdirectorios dentro de 'logs/'
    for carpeta in carpetas_logs:
        if os.path.exists(carpeta):
            for entry in os.listdir(carpeta):
                path = os.path.join(carpeta, entry)
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                        logger.info(f"Archivo eliminado: {path}")
                    elif os.path.isdir(path):
                        shutil.rmtree(path)
                        logger.info(f"Directorio eliminado: {path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar {path}: {e}")

    logger.info("\n✔️ Limpieza completada correctamente.")

if __name__ == "__main__":
    limpiar_logs()
