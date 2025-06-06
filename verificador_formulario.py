import logging
from typing import List
from playwright.sync_api import Page

logger = logging.getLogger("verificador_formulario")


def formulario_completo(page: Page, campos_requeridos: List[str]) -> bool:
    """
    Verifica secuencialmente que cada selector esté presente, visible, habilitado y no vacío.
    Detecta inputs, selects y checkboxes.
    """
    for selector in campos_requeridos:
        try:
            # Localizar y esperar a que el elemento esté adjunto al DOM
            el = page.locator(selector)
            el.wait_for(state="attached", timeout=30000)

            # Verificar visibilidad y habilitación
            if not el.is_visible():
                logger.warning(f"{selector} no está visible")
                return False
            if not el.is_enabled():
                logger.warning(f"{selector} no está habilitado")
                return False

            # Determinar tipo de elemento
            tag = el.evaluate("el => el.tagName").lower()
            if tag == "select":
                # Para <select>, verificar valor seleccionado
                val = el.evaluate("el => el.value")
                if not val:
                    logger.warning(f"{selector} (select) no tiene valor seleccionado")
                    return False

            elif tag == "input":
                # Para <input>, diferenciar checkbox de otros tipos
                type_ = el.evaluate("el => el.type").lower()
                if type_ == "checkbox":
                    checked = el.evaluate("el => el.checked")
                    if not checked:
                        logger.warning(f"{selector} (checkbox) no está marcado")
                        return False
                else:
                    # Otros inputs: verificar valor de entrada
                    val = el.input_value().strip()
                    if not val:
                        logger.warning(f"{selector} (input) está vacío")
                        return False

            else:
                # Para otros tags, verificar contenido de texto
                text = el.evaluate("el => el.textContent").strip()
                if not text:
                    logger.warning(f"{selector} ({tag}) está vacío")
                    return False

        except Exception as e:
            logger.warning(f"Error verificando {selector}: {e}")
            return False

    return True
