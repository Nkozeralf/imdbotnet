"""
CRUD Stores Module - Gestión completa de tiendas
Crear, leer, actualizar y eliminar configuraciones de tiendas
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import requests
from datetime import datetime

class StoreCRUD:
    """Clase para operaciones CRUD de tiendas"""
    
    def __init__(self):
        self.stores_dir = Path(__file__).parent.parent / "tiendas"
        self.stores_dir.mkdir(exist_ok=True)
        
        # Plantilla para nuevas tiendas
        self.store_template = {
            "url_producto": "",
            "detecta_popup": True,
            "emulate_mobile": False,
            "boton_popup": "",
            "popup_formulario": "",
            "campos": {},
            "selects": [],
            "departamento_valores": [],
            "checkbox": None,
            "campos_requeridos": [],
            "boton_envio": "",
            "order_id_selector": "",
            "timeouts": {
                "popup_wait": 30000,
                "form_wait": 30000,
                "city_load_wait": 15000,
                "submit_wait": 60000
            },
            "cantidad_ofertas": {
                "selector_contenedor": "",
                "ofertas": []
            }
        }
        
        # Inicializar estado de sesión
        if 'selected_store' not in st.session_state:
            st.session_state.selected_store = None
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        if 'store_form_data' not in st.session_state:
            st.session_state.store_form_data = {}
    
    @staticmethod
    def list_stores() -> List[str]:
        """Listar todas las tiendas disponibles"""
        stores_dir = Path(__file__).parent.parent / "tiendas"
        if not stores_dir.exists():
            return []
        
        stores = []
        for file in stores_dir.glob("*.json"):
            stores.append(file.stem)
        
        return sorted(stores)
    
    def load_store(self, store_name: str) -> Optional[Dict]:
        """Cargar configuración de una tienda"""
        store_path = self.stores_dir / f"{store_name}.json"
        
        if not store_path.exists():
            return None
        
        try:
            with open(store_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error cargando tienda {store_name}: {e}")
            return None
    
    def save_store(self, store_name: str, config: Dict) -> bool:
        """Guardar configuración de una tienda"""
        if not store_name or not store_name.strip():
            st.error("El nombre de la tienda no puede estar vacío")
            return False
        
        # Validar nombre (solo caracteres alfanuméricos y guiones)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', store_name):
            st.error("El nombre solo puede contener letras, números, guiones y guiones bajos")
            return False
        
        store_path = self.stores_dir / f"{store_name}.json"
        
        try:
            # Validar configuración básica
            if not self.validate_store_config(config):
                return False
            
            # Guardar archivo
            with open(store_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            st.success(f"✅ Tienda '{store_name}' guardada exitosamente")
            return True
            
        except Exception as e:
            st.error(f"Error guardando tienda: {e}")
            return False
    
    def delete_store(self, store_name: str) -> bool:
        """Eliminar una tienda"""
        store_path = self.stores_dir / f"{store_name}.json"
        
        if not store_path.exists():
            st.error(f"La tienda '{store_name}' no existe")
            return False
        
        try:
            store_path.unlink()
            st.success(f"✅ Tienda '{store_name}' eliminada exitosamente")
            return True
        except Exception as e:
            st.error(f"Error eliminando tienda: {e}")
            return False
    
    def validate_store_config(self, config: Dict) -> bool:
        """Validar configuración de tienda"""
        required_fields = ['url_producto', 'detecta_popup', 'boton_envio']
        
        for field in required_fields:
            if field not in config:
                st.error(f"Campo requerido faltante: {field}")
                return False
        
        # Validar URL
        url = config.get('url_producto', '')
        if not url.startswith(('http://', 'https://')):
            st.error("La URL del producto debe comenzar con http:// o https://")
            return False
        
        return True
    
    def test_store_url(self, url: str) -> bool:
        """Probar si una URL de tienda es accesible"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code < 400
        except:
            return False
    
    def render_store_list(self):
        """Renderizar lista de tiendas"""
        st.subheader("📋 Lista de Tiendas")
        
        stores = self.list_stores()
        
        if not stores:
            st.info("📭 No hay tiendas configuradas. Crea tu primera tienda.")
            return
        
        # Crear tabla de tiendas
        for store_name in stores:
            with st.expander(f"🏪 {store_name}", expanded=False):
                config = self.load_store(store_name)
                
                if config:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**URL:** {config.get('url_producto', 'N/A')[:50]}...")
                        st.write(f"**Mobile:** {'Sí' if config.get('emulate_mobile') else 'No'}")
                        st.write(f"**Popup:** {'Sí' if config.get('detecta_popup') else 'No'}")
                    
                    with col2:
                        if st.button("✏️ Editar", key=f"edit_{store_name}"):
                            st.session_state.selected_store = store_name
                            st.session_state.edit_mode = True
                            st.session_state.store_form_data = config.copy()
                            st.rerun()
                    
                    with col3:
                        if st.button("🧪 Probar", key=f"test_{store_name}"):
                            with st.spinner("Probando URL..."):
                                url = config.get('url_producto', '')
                                if self.test_store_url(url):
                                    st.success("✅ URL accesible")
                                else:
                                    st.error("❌ URL no accesible")
                    
                    with col4:
                        if st.button("🗑️ Eliminar", key=f"delete_{store_name}"):
                            if st.session_state.get(f'confirm_delete_{store_name}'):
                                if self.delete_store(store_name):
                                    st.rerun()
                            else:
                                st.session_state[f'confirm_delete_{store_name}'] = True
                                st.warning("⚠️ Haz clic nuevamente para confirmar")
                else:
                    st.error("❌ Error cargando configuración")
    
    def render_store_form(self, store_name: str = None, config: Dict = None):
        """Renderizar formulario de tienda"""
        is_edit = store_name is not None
        title = f"✏️ Editando: {store_name}" if is_edit else "➕ Nueva Tienda"
        
        st.subheader(title)
        
        # Usar configuración existente o plantilla
        if config is None:
            config = self.store_template.copy()
        
        with st.form("store_form"):
            # Información básica
            st.markdown("### 📝 Información Básica")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if is_edit:
                    st.text_input("Nombre de la tienda", value=store_name, disabled=True)
                    form_store_name = store_name
                else:
                    form_store_name = st.text_input(
                        "Nombre de la tienda",
                        placeholder="Ej: mitienda",
                        help="Solo letras, números, guiones y guiones bajos"
                    )
                
                url_producto = st.text_input(
                    "URL del producto",
                    value=config.get('url_producto', ''),
                    placeholder="https://mitienda.com/products/mi-producto"
                )
            
            with col2:
                emulate_mobile = st.checkbox(
                    "Emular móvil",
                    value=config.get('emulate_mobile', False),
                    help="Usar viewport móvil para la navegación"
                )
                
                detecta_popup = st.checkbox(
                    "Detectar popup",
                    value=config.get('detecta_popup', True),
                    help="La tienda usa popup para el formulario"
                )
            
            # Configuración de popup
            st.markdown("### 🪟 Configuración de Popup")
            
            col1, col2 = st.columns(2)
            
            with col1:
                boton_popup = st.text_input(
                    "Selector del botón popup",
                    value=config.get('boton_popup', ''),
                    placeholder="Ej: #buy-now-button",
                    disabled=not detecta_popup
                )
            
            with col2:
                popup_formulario = st.text_input(
                    "Selector del formulario popup",
                    value=config.get('popup_formulario', ''),
                    placeholder="Ej: #popup-form",
                    disabled=not detecta_popup
                )
            
            # Configuración de campos
            st.markdown("### 📋 Campos del Formulario")
            
            # Editor simple de campos
            campos_json = st.text_area(
                "Configuración de campos (JSON)",
                value=json.dumps(config.get('campos', {}), indent=2),
                height=150,
                help="Mapeo de selectores CSS a nombres de campos"
            )
            
            # Configuración de selects
            st.markdown("### 📍 Selects (Departamento/Ciudad)")
            
            selects_json = st.text_area(
                "Configuración de selects (JSON)",
                value=json.dumps(config.get('selects', []), indent=2),
                height=100,
                help="Configuración de campos select"
            )
            
            # Valores de departamento
            departamento_valores = st.text_area(
                "Valores de departamento (uno por línea)",
                value='\n'.join(config.get('departamento_valores', [])),
                help="Lista de códigos de departamento"
            )
            
            # Configuración final
            st.markdown("### ⚙️ Configuración Final")
            
            col1, col2 = st.columns(2)
            
            with col1:
                boton_envio = st.text_input(
                    "Selector del botón de envío",
                    value=config.get('boton_envio', ''),
                    placeholder="Ej: #submit-button"
                )
                
                checkbox = st.text_input(
                    "Selector del checkbox (opcional)",
                    value=config.get('checkbox', '') or '',
                    placeholder="Ej: #terms-checkbox"
                )
            
            with col2:
                order_id_selector = st.text_input(
                    "Selector del Order ID",
                    value=config.get('order_id_selector', ''),
                    placeholder="Ej: .order-number"
                )
            
            # Timeouts
            st.markdown("### ⏱️ Timeouts (ms)")
            
            col1, col2, col3, col4 = st.columns(4)
            
            timeouts = config.get('timeouts', {})
            
            with col1:
                popup_wait = st.number_input(
                    "Espera popup",
                    value=timeouts.get('popup_wait', 30000),
                    min_value=1000,
                    max_value=120000,
                    step=1000
                )
            
            with col2:
                form_wait = st.number_input(
                    "Espera formulario",
                    value=timeouts.get('form_wait', 30000),
                    min_value=1000,
                    max_value=120000,
                    step=1000
                )
            
            with col3:
                city_load_wait = st.number_input(
                    "Carga ciudades",
                    value=timeouts.get('city_load_wait', 15000),
                    min_value=1000,
                    max_value=60000,
                    step=1000
                )
            
            with col4:
                submit_wait = st.number_input(
                    "Espera envío",
                    value=timeouts.get('submit_wait', 60000),
                    min_value=5000,
                    max_value=300000,
                    step=5000
                )
            
            # Botones del formulario
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                submit = st.form_submit_button("💾 Guardar", type="primary")
            
            with col2:
                if is_edit:
                    cancel = st.form_submit_button("❌ Cancelar")
                else:
                    clear = st.form_submit_button("🧹 Limpiar")
            
            # Procesar envío del formulario
            if submit:
                # Validar nombre
                if not form_store_name or not form_store_name.strip():
                    st.error("El nombre de la tienda es requerido")
                    return
                
                # Validar URL
                if not url_producto or not url_producto.startswith(('http://', 'https://')):
                    st.error("URL de producto inválida")
                    return
                
                # Construir configuración
                try:
                    new_config = {
                        'url_producto': url_producto,
                        'detecta_popup': detecta_popup,
                        'emulate_mobile': emulate_mobile,
                        'boton_popup': boton_popup if detecta_popup else '',
                        'popup_formulario': popup_formulario if detecta_popup else '',
                        'campos': json.loads(campos_json) if campos_json.strip() else {},
                        'selects': json.loads(selects_json) if selects_json.strip() else [],
                        'departamento_valores': [d.strip() for d in departamento_valores.split('\n') if d.strip()],
                        'checkbox': checkbox if checkbox.strip() else None,
                        'campos_requeridos': [],  # Se puede configurar después
                        'boton_envio': boton_envio,
                        'order_id_selector': order_id_selector,
                        'timeouts': {
                            'popup_wait': popup_wait,
                            'form_wait': form_wait,
                            'city_load_wait': city_load_wait,
                            'submit_wait': submit_wait
                        },
                        'cantidad_ofertas': config.get('cantidad_ofertas', {
                            'selector_contenedor': '',
                            'ofertas': []
                        })
                    }
                    
                    # Guardar tienda
                    if self.save_store(form_store_name.strip(), new_config):
                        # Limpiar estado
                        st.session_state.selected_store = None
                        st.session_state.edit_mode = False
                        st.session_state.store_form_data = {}
                        st.rerun()
                
                except json.JSONDecodeError as e:
                    st.error(f"Error en formato JSON: {e}")
                except Exception as e:
                    st.error(f"Error guardando configuración: {e}")
            
            elif is_edit and cancel:
                # Cancelar edición
                st.session_state.selected_store = None
                st.session_state.edit_mode = False
                st.session_state.store_form_data = {}
                st.rerun()
            
            elif not is_edit and clear:
                # Limpiar formulario
                st.session_state.store_form_data = {}
                st.rerun()
    
    def render(self):
        """Renderizar componente completo de CRUD"""
        # Tabs principales
        tab1, tab2 = st.tabs(["📋 Lista de Tiendas", "➕ Crear/Editar Tienda"])
        
        with tab1:
            self.render_store_list()
            
            # Botón para crear nueva tienda
            st.divider()
            if st.button("➕ Crear Nueva Tienda", type="primary"):
                st.session_state.selected_store = None
                st.session_state.edit_mode = False
                st.session_state.store_form_data = {}
                # Cambiar a la tab de crear/editar
                st.switch_page
        
        with tab2:
            # Mostrar formulario de edición o creación
            if st.session_state.edit_mode and st.session_state.selected_store:
                # Modo edición
                config = st.session_state.store_form_data
                self.render_store_form(
                    st.session_state.selected_store, 
                    config
                )
            else:
                # Modo creación
                self.render_store_form()
        
        # Información de ayuda
        with st.expander("ℹ️ Ayuda - Configuración de Tiendas"):
            st.markdown("""
            ### 📖 Guía de Configuración
            
            **Campos importantes:**
            - **URL del producto**: URL directa del producto donde aparece el botón de compra
            - **Selector del botón popup**: CSS selector del botón que abre el popup (ej: `#buy-now`)
            - **Selector del formulario**: CSS selector del formulario dentro del popup
            
            **Configuración de campos:**
            ```json
            {
                "#field-name": "nombre",
                "#field-email": "email",
                "#field-phone": "telefono"
            }
            ```
            
            **Configuración de selects:**
            ```json
            [
                {
                    "selector": "#province-select",
                    "valor": "departamento"
                },
                {
                    "selector": "#city-select", 
                    "valor": "ciudad"
                }
            ]
            ```
            
            **Tips:**
            - Usa las herramientas de desarrollador del navegador (F12) para encontrar selectores
            - Prueba la URL antes de guardar para verificar accesibilidad
            - Los timeouts están en milisegundos (1000ms = 1 segundo)
            """)
