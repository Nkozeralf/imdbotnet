import streamlit as st
import subprocess
import json
import os
from pathlib import Path

st.set_page_config(page_title="🚀 Shopify Bot", layout="wide")

# Rutas
BOT_PATH = "/home/botexecutor/shopify-bot"
TIENDAS_PATH = f"{BOT_PATH}/tiendas"

def run_command(cmd):
    """Ejecutar comando simple"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=BOT_PATH)
        return result.stdout, result.stderr, result.returncode
    except:
        return "", "Error ejecutando comando", 1

def get_tiendas():
    """Obtener tiendas"""
    try:
        tiendas = []
        for file in os.listdir(TIENDAS_PATH):
            if file.endswith('.json'):
                tiendas.append(file.replace('.json', ''))
        return sorted(tiendas)
    except:
        return []

def load_tienda(nombre):
    """Cargar tienda"""
    try:
        with open(f"{TIENDAS_PATH}/{nombre}.json", 'r') as f:
            return json.load(f)
    except:
        return None

def save_tienda(nombre, config):
    """Guardar tienda"""
    try:
        with open(f"{TIENDAS_PATH}/{nombre}.json", 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

def delete_tienda(nombre):
    """Eliminar tienda"""
    try:
        os.remove(f"{TIENDAS_PATH}/{nombre}.json")
        return True
    except:
        return False

# TÍTULO
st.title("🚀 Shopify Bot Dashboard")

# SIDEBAR
st.sidebar.title("📋 Menú")
page = st.sidebar.radio("Sección", ["💻 Consola", "🏪 Tiendas"])

# BOTÓN PARAR
if st.sidebar.button("🛑 PARAR BOT", type="primary"):
    run_command("pkill -f launcher.py")
    run_command("pkill -f playwright")
    st.sidebar.success("✅ Bot parado")

# ===============================
# PÁGINA CONSOLA
# ===============================
if page == "💻 Consola":
    st.header("💻 Consola Web")
    
    # Comandos predefinidos
    st.subheader("🔧 Comandos Rápidos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Ejecutar Bot", use_container_width=True):
            st.info("Ejecutando bot...")
            cmd = f"cd {BOT_PATH} && source /home/botexecutor/venv-playwright/bin/activate && python launcher.py"
            
            # Crear script temporal
            script = f"""#!/bin/bash
{cmd} > /tmp/bot_log.txt 2>&1 &
echo $! > /tmp/bot_pid.txt
"""
            with open("/tmp/run_bot.sh", "w") as f:
                f.write(script)
            os.chmod("/tmp/run_bot.sh", 0o755)
            
            # Ejecutar
            stdout, stderr, code = run_command("/tmp/run_bot.sh")
            
            if code == 0:
                st.success("✅ Bot iniciado")
                st.info("📝 Log en /tmp/bot_log.txt")
            else:
                st.error(f"❌ Error: {stderr}")
    
    with col2:
        if st.button("📝 Ver Log", use_container_width=True):
            stdout, stderr, code = run_command("tail -10 /tmp/bot_log.txt 2>/dev/null || echo 'No hay log'")
            st.code(stdout)
    
    with col3:
        if st.button("📊 Ver Procesos", use_container_width=True):
            stdout, stderr, code = run_command("ps aux | grep launcher | grep -v grep")
            if stdout:
                st.code(stdout)
            else:
                st.info("No hay procesos corriendo")
    
    st.markdown("---")
    
    # Comando personalizado
    st.subheader("⌨️ Comando Personalizado")
    
    comando = st.text_input("Comando:", placeholder="ls -la")
    
    if st.button("▶️ Ejecutar") and comando:
        with st.spinner("Ejecutando..."):
            stdout, stderr, code = run_command(comando)
            
            if stdout:
                st.code(stdout)
            
            if stderr:
                st.error(stderr)
    
    st.markdown("---")
    
    # Ejecutar bot con opciones
    st.subheader("🎯 Ejecutar Bot con Opciones")
    
    tiendas_disponibles = get_tiendas()
    
    if tiendas_disponibles:
        # Selección de tiendas
        tiendas_seleccionadas = st.multiselect("Tiendas:", tiendas_disponibles)
        
        # Opciones
        col1, col2 = st.columns(2)
        with col1:
            pedidos = st.number_input("Pedidos por tienda:", 1, 5, 1)
            usar_proxy = st.checkbox("Usar proxy", True)
        
        with col2:
            modo_rapido = st.checkbox("Modo rápido", False)
            usar_intervalos = st.checkbox("Usar intervalos", True)
        
        # Botón ejecutar
        if st.button("🚀 EJECUTAR PEDIDOS", type="primary") and tiendas_seleccionadas:
            # Crear input automático
            todas_tiendas = get_tiendas()
            indices = []
            
            for tienda in tiendas_seleccionadas:
                if tienda in todas_tiendas:
                    idx = todas_tiendas.index(tienda) + 1
                    indices.append(str(idx))
            
            input_auto = f"""n
{','.join(indices)}
{pedidos}
{'s' if usar_proxy else 'n'}
{'s' if modo_rapido else 'n'}
{'intervalos' if usar_intervalos else 'inmediato'}
s
"""
            
            # Crear script
            script_bot = f"""#!/bin/bash
cd {BOT_PATH}
source /home/botexecutor/venv-playwright/bin/activate
echo '{input_auto}' | python launcher.py > /tmp/bot_pedidos.log 2>&1 &
echo $! > /tmp/bot_pedidos_pid.txt
"""
            
            with open("/tmp/ejecutar_pedidos.sh", "w") as f:
                f.write(script_bot)
            os.chmod("/tmp/ejecutar_pedidos.sh", 0o755)
            
            # Ejecutar
            stdout, stderr, code = run_command("/tmp/ejecutar_pedidos.sh")
            
            if code == 0:
                st.success("✅ Pedidos ejecutándose")
                st.info(f"📦 {len(tiendas_seleccionadas)} tiendas, {pedidos} pedidos cada una")
                st.info("📝 Log: /tmp/bot_pedidos.log")
            else:
                st.error("❌ Error ejecutando pedidos")
    else:
        st.warning("⚠️ No hay tiendas configuradas")

# ===============================
# PÁGINA TIENDAS
# ===============================
elif page == "🏪 Tiendas":
    st.header("🏪 Gestión de Tiendas")
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver", "➕ Crear", "✏️ Editar"])
    
    # VER TIENDAS
    with tab1:
        tiendas = get_tiendas()
        
        if tiendas:
            for tienda in tiendas:
                config = load_tienda(tienda)
                
                with st.expander(f"🏪 {tienda}"):
                    if config:
                        st.write(f"🔗 **URL:** {config.get('url_producto', 'No definida')}")
                        st.write(f"📱 **Mobile:** {'Sí' if config.get('emulate_mobile') else 'No'}")
                        st.write(f"🪟 **Popup:** {'Sí' if config.get('detecta_popup') else 'No'}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"📄 Ver JSON", key=f"view_{tienda}"):
                                st.json(config)
                        
                        with col2:
                            if st.button(f"🗑️ Eliminar", key=f"del_{tienda}"):
                                if delete_tienda(tienda):
                                    st.success(f"Eliminada: {tienda}")
                                    st.rerun()
                    else:
                        st.error("Error cargando configuración")
        else:
            st.info("📭 No hay tiendas configuradas")
    
    # CREAR TIENDA
    with tab2:
        st.subheader("➕ Crear Nueva Tienda")
        
        with st.form("nueva_tienda"):
            nombre = st.text_input("Nombre de la tienda:")
            url = st.text_input("URL del producto:")
            
            st.write("**Opciones:**")
            mobile = st.checkbox("Emular móvil")
            popup = st.checkbox("Detecta popup")
            
            if st.form_submit_button("💾 Crear Tienda"):
                if nombre and url:
                    config = {
                        "url_producto": url,
                        "emulate_mobile": mobile,
                        "detecta_popup": popup,
                        "boton_popup": "",
                        "popup_formulario": "",
                        "campos": {},
                        "selects": [],
                        "timeouts": {
                            "popup_wait": 30000,
                            "form_wait": 30000,
                            "submit_wait": 60000
                        }
                    }
                    
                    if save_tienda(nombre, config):
                        st.success(f"✅ Tienda '{nombre}' creada")
                        st.rerun()
                    else:
                        st.error("❌ Error guardando tienda")
                else:
                    st.warning("⚠️ Completa nombre y URL")
    
    # EDITAR TIENDA
    with tab3:
        tiendas = get_tiendas()
        
        if tiendas:
            tienda_editar = st.selectbox("Seleccionar tienda:", tiendas)
            
            if tienda_editar:
                config = load_tienda(tienda_editar)
                
                if config:
                    st.subheader(f"✏️ Editando: {tienda_editar}")
                    
                    config_json = st.text_area(
                        "Configuración JSON:",
                        value=json.dumps(config, indent=2),
                        height=400
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("💾 Guardar"):
                            try:
                                nueva_config = json.loads(config_json)
                                if save_tienda(tienda_editar, nueva_config):
                                    st.success("✅ Tienda actualizada")
                                    st.rerun()
                                else:
                                    st.error("❌ Error guardando")
                            except json.JSONDecodeError:
                                st.error("❌ JSON inválido")
                    
                    with col2:
                        if st.button("🔄 Recargar"):
                            st.rerun()
                else:
                    st.error("❌ Error cargando tienda")
        else:
            st.info("📭 No hay tiendas para editar")

# FOOTER
st.sidebar.markdown("---")
st.sidebar.caption("🚀 Dashboard Simple")
st.sidebar.caption("💻 Sin errores")
st.sidebar.caption(f"📂 {BOT_PATH}")
