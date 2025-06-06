#!/usr/bin/env python3
# streamlit_dashboard/dashboard.py

import streamlit as st
import subprocess
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import glob
from pathlib import Path
import re

# Configuración de página
st.set_page_config(
    page_title="🚀 Shopify Bot Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class ShopifyBotController:
    def __init__(self):
        self.bot_path = Path.home() / "shopify-bot"
        self.logs_path = self.bot_path / "logs"
        self.tiendas_path = self.bot_path / "tiendas"
        
    def get_available_tiendas(self):
        """Obtener tiendas disponibles desde archivos JSON en orden alfabético"""
        try:
            if not self.tiendas_path.exists():
                return []
            
            tiendas = []
            for json_file in self.tiendas_path.glob("*.json"):
                tienda_name = json_file.stem
                tiendas.append(tienda_name)
            
            # Ordenar alfabéticamente para consistencia
            tiendas_ordenadas = sorted(tiendas)
            
            # Log para debugging
            print(f"🔍 Tiendas encontradas en orden: {tiendas_ordenadas}")
            
            return tiendas_ordenadas
        except Exception as e:
            st.error(f"Error leyendo tiendas: {e}")
            return []
    
    def load_tienda_config(self, tienda_name):
        """Cargar configuración de una tienda"""
        try:
            config_file = self.tiendas_path / f"{tienda_name}.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            st.error(f"Error cargando configuración de {tienda_name}: {e}")
            return None
    
    def execute_bot(self, tiendas, pedidos_por_tienda, usar_proxy, modo_rapido, usar_intervalos):
        """Ejecutar el bot con parámetros específicos"""
        try:
            # Cambiar al directorio del bot
            os.chdir(self.bot_path)
            
            # Determinar qué launcher usar
            launcher_file = "launcher_mejorado.py" if (self.bot_path / "launcher_mejorado.py").exists() else "launcher.py"
            
            # Crear input para el bot (simulando entradas del usuario)
            input_data = "n\n"  # No limpiar logs
            
            # Seleccionar tiendas por número
            available_tiendas = self.get_available_tiendas()
            tienda_indices = []
            
            # DEBUG: Mostrar mapeo de tiendas
            st.write("🔍 DEBUG - Mapeo de tiendas:")
            for i, tienda_disponible in enumerate(available_tiendas):
                status = "✅ SELECCIONADA" if tienda_disponible in tiendas else "⭕ No seleccionada"
                st.write(f"  {i+1}. {tienda_disponible} - {status}")
            
            for tienda in tiendas:
                if tienda in available_tiendas:
                    indice = available_tiendas.index(tienda) + 1
                    tienda_indices.append(str(indice))
                    st.write(f"🎯 Tienda '{tienda}' -> Índice {indice}")
            
            if not tienda_indices:
                st.error(f"❌ No se encontraron índices para tiendas: {tiendas}")
                st.error(f"Tiendas disponibles: {available_tiendas}")
                return None, None
            
            input_data += ",".join(tienda_indices) + "\n"
            input_data += f"{pedidos_por_tienda}\n"
            input_data += "s\n" if usar_proxy else "n\n"
            input_data += "s\n" if modo_rapido else "n\n"
            
            # Modo de ejecución
            if usar_intervalos:
                input_data += "intervalos\n"
            else:
                input_data += "inmediato\n"
            
            input_data += "s\n"  # Confirmar
            
            # Crear comando bash que active el entorno virtual y ejecute
            bash_command = f"""
            cd {self.bot_path}
            source ~/venv-playwright/bin/activate
            echo '{input_data}' | python {launcher_file}
            """
            
            return bash_command, input_data
            
        except Exception as e:
            st.error(f"Error preparando ejecución: {e}")
            return None, None
    
    def execute_bot_async(self, bash_command):
        """Ejecutar el bot de forma asíncrona"""
        try:
            import threading
            import subprocess
            
            def run_bot():
                try:
                    # Ejecutar el comando bash
                    process = subprocess.Popen(
                        bash_command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=str(self.bot_path)
                    )
                    
                    # Capturar output en tiempo real
                    stdout, stderr = process.communicate()
                    
                    # Guardar output para debugging
                    with open(self.bot_path / "last_execution.log", "w", encoding="utf-8") as f:
                        f.write(f"=== EJECUCIÓN {datetime.now()} ===\n")
                        f.write(f"COMANDO: {bash_command}\n")
                        f.write(f"CÓDIGO SALIDA: {process.returncode}\n")
                        f.write(f"STDOUT:\n{stdout}\n")
                        f.write(f"STDERR:\n{stderr}\n")
                        f.write("=" * 50 + "\n")
                    
                    return process.returncode == 0
                    
                except Exception as e:
                    error_msg = f"Error ejecutando bot: {str(e)}"
                    with open(self.bot_path / "execution_error.log", "w", encoding="utf-8") as f:
                        f.write(f"{datetime.now()}: {error_msg}\n")
                    return False
            
            # Ejecutar en hilo separado
            thread = threading.Thread(target=run_bot, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            st.error(f"Error iniciando ejecución: {e}")
            return False
    
    def get_recent_logs(self, limit=100):
        """Obtener logs recientes"""
        try:
            log_files = []
            if self.logs_path.exists():
                for log_file in self.logs_path.glob("*.log"):
                    log_files.append(log_file)
            
            # Ordenar por fecha de modificación
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            recent_logs = []
            for log_file in log_files[:3]:  # Últimos 3 archivos de log
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        recent_logs.extend(lines[-limit//3:])  # Dividir el límite entre archivos
                except:
                    continue
            
            return recent_logs[-limit:]
        except Exception as e:
            return [f"Error leyendo logs: {e}"]
    
    def get_statistics(self):
        """Obtener estadísticas de los logs"""
        try:
            logs = self.get_recent_logs(1000)
            
            stats = {
                'total_intentos': 0,
                'exitos': 0,
                'fallos': 0,
                'en_progreso': 0,
                'last_execution': None
            }
            
            for line in logs:
                if '✅' in line or 'exitoso' in line.lower():
                    stats['exitos'] += 1
                elif '❌' in line or 'error' in line.lower() or 'fallo' in line.lower():
                    stats['fallos'] += 1
                elif '🚀' in line or 'iniciando' in line.lower():
                    stats['en_progreso'] += 1
                
                # Buscar timestamp más reciente
                timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
                if timestamp_match:
                    stats['last_execution'] = timestamp_match.group()
            
            stats['total_intentos'] = stats['exitos'] + stats['fallos']
            
            return stats
        except Exception as e:
            return {
                'total_intentos': 0,
                'exitos': 0,
                'fallos': 0,
                'en_progreso': 0,
                'last_execution': 'Error obteniendo datos'
            }
    
    def get_screenshots(self):
        """Obtener screenshots recientes"""
        try:
            screenshots = []
            if self.logs_path.exists():
                for tienda_dir in self.logs_path.iterdir():
                    if tienda_dir.is_dir():
                        for img_file in tienda_dir.glob("*.png"):
                            screenshots.append({
                                'file': img_file,
                                'tienda': tienda_dir.name,
                                'timestamp': datetime.fromtimestamp(img_file.stat().st_mtime),
                                'size': img_file.stat().st_size
                            })
            
            # Ordenar por timestamp
            screenshots.sort(key=lambda x: x['timestamp'], reverse=True)
            return screenshots[:10]  # Últimos 10
        except Exception as e:
            return []

# Inicializar controlador
controller = ShopifyBotController()

# Sidebar con navegación
st.sidebar.title("🚀 Shopify Bot")
st.sidebar.markdown("---")

page = st.sidebar.selectbox(
    "Navegación",
    ["🎛️ Panel de Control", "📊 Estadísticas", "📝 Logs en Vivo", "🔧 Configuración", "📸 Screenshots"]
)

# Página principal: Panel de Control
if page == "🎛️ Panel de Control":
    st.markdown('<h1 class="main-header">🎛️ Panel de Control</h1>', unsafe_allow_html=True)
    
    # Obtener estadísticas para mostrar estado actual
    stats = controller.get_statistics()
    
    # Métricas en tiempo real
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Intentos",
            value=stats['total_intentos'],
            delta=f"Éxitos: {stats['exitos']}"
        )
    
    with col2:
        success_rate = (stats['exitos'] / max(stats['total_intentos'], 1)) * 100
        st.metric(
            label="✅ Tasa de Éxito",
            value=f"{success_rate:.1f}%",
            delta=f"Éxitos: {stats['exitos']}"
        )
    
    with col3:
        st.metric(
            label="❌ Fallos",
            value=stats['fallos'],
            delta="Recientes"
        )
    
    with col4:
        st.metric(
            label="🔄 En Progreso",
            value=stats['en_progreso'],
            delta="Activos"
        )
    
    st.markdown("---")
    
    # Formulario de configuración
    st.subheader("⚙️ Configuración de Ejecución")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏪 Selección de Tiendas**")
        available_tiendas = controller.get_available_tiendas()
        
        if available_tiendas:
            selected_tiendas = st.multiselect(
                "Tiendas disponibles:",
                available_tiendas,
                default=[available_tiendas[0]] if available_tiendas else []
            )
            
            # Mostrar información de tiendas seleccionadas
            if selected_tiendas:
                st.info(f"✅ {len(selected_tiendas)} tienda(s) seleccionada(s)")
                for tienda in selected_tiendas:
                    config = controller.load_tienda_config(tienda)
                    if config:
                        url = config.get('url_producto', 'No disponible')
                        st.caption(f"🔗 {tienda}: {url[:50]}...")
        else:
            st.error("❌ No se encontraron tiendas. Verificar directorio 'tiendas/'")
            selected_tiendas = []
        
        pedidos_por_tienda = st.number_input(
            "📦 Pedidos por tienda:",
            min_value=1,
            max_value=100,
            value=1,
            help="Número de pedidos a generar por cada tienda seleccionada"
        )
    
    with col2:
        st.markdown("**🔧 Opciones Avanzadas**")
        
        usar_proxy = st.checkbox(
            "🌐 Usar Proxy Service",
            value=True,
            help="Utilizar servicio de proxy colombiano"
        )
        
        modo_rapido = st.checkbox(
            "⚡ Modo Rápido",
            value=False,
            help="Ejecutar sin imágenes ni delays adicionales"
        )
        
        total_pedidos = len(selected_tiendas) * pedidos_por_tienda
        
        if total_pedidos <= 10:
            usar_intervalos = st.radio(
                "⏱️ Modo de Ejecución:",
                ["inmediato", "intervalos"],
                help="Inmediato: ejecuta todos los pedidos rápidamente. Intervalos: espaciados en 1-10 min"
            ) == "intervalos"
        else:
            usar_intervalos = st.checkbox(
                "⏱️ Usar Intervalos Aleatorios (1-10 min)",
                value=True,
                help="Recomendado para más de 10 pedidos"
            )
        
        # Información del plan de ejecución
        st.info(f"""
        📋 **Plan de Ejecución:**
        - 🏪 Tiendas: {len(selected_tiendas)}
        - 📦 Total pedidos: {total_pedidos}
        - ⏱️ Modo: {'Intervalos' if usar_intervalos else 'Inmediato'}
        - 🌐 Proxy: {'Activado' if usar_proxy else 'Desactivado'}
        """)
    
    st.markdown("---")
    
    # Botón de ejecución
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button(
            "🚀 EJECUTAR PEDIDOS",
            type="primary",
            use_container_width=True,
            disabled=not selected_tiendas
        ):
            if selected_tiendas:
                with st.spinner("🔄 Preparando ejecución..."):
                    cmd, input_data = controller.execute_bot(
                        selected_tiendas,
                        pedidos_por_tienda,
                        usar_proxy,
                        modo_rapido,
                        usar_intervalos
                    )
                    
                    if cmd:
                        # Ejecutar el bot realmente
                        if controller.execute_bot_async(cmd):
                            st.success("✅ Bot ejecutándose en segundo plano!")
                            st.info("🎯 Revisa la pestaña 'Logs en Vivo' para monitorear el progreso.")
                            st.info("📁 También puedes revisar el archivo 'last_execution.log' para detalles.")
                            
                            # Mostrar comando que se ejecutó (para debug)
                            with st.expander("🔍 Ver comando ejecutado (Debug)"):
                                st.code(f"Comando ejecutado:\n{cmd}")
                                st.code(f"Input simulado:\n{repr(input_data)}")
                                
                            # Crear un indicador de que hay una ejecución en progreso
                            st.session_state['bot_running'] = True
                            st.session_state['execution_time'] = datetime.now()
                            
                        else:
                            st.error("❌ Error ejecutando el bot")
                    else:
                        st.error("❌ Error preparando la ejecución")
            else:
                st.warning("⚠️ Selecciona al menos una tienda")

# Página de Estadísticas
elif page == "📊 Estadísticas":
    st.markdown('<h1 class="main-header">📊 Estadísticas en Tiempo Real</h1>', unsafe_allow_html=True)
    
    # Auto-refresh cada 10 segundos
    if st.button("🔄 Actualizar Datos"):
        st.rerun()
    
    stats = controller.get_statistics()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Intentos", stats['total_intentos'])
    with col2:
        st.metric("✅ Éxitos", stats['exitos'])
    with col3:
        st.metric("❌ Fallos", stats['fallos'])
    with col4:
        success_rate = (stats['exitos'] / max(stats['total_intentos'], 1)) * 100
        st.metric("📈 Tasa Éxito", f"{success_rate:.1f}%")
    
    # Gráfico de torta
    if stats['total_intentos'] > 0:
        fig = px.pie(
            values=[stats['exitos'], stats['fallos']],
            names=['Éxitos', 'Fallos'],
            title="Distribución de Resultados",
            color_discrete_map={'Éxitos': '#28a745', 'Fallos': '#dc3545'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Última ejecución
    if stats['last_execution']:
        st.info(f"🕒 Última ejecución: {stats['last_execution']}")

# Página de Logs
elif page == "📝 Logs en Vivo":
    st.markdown('<h1 class="main-header">📝 Logs en Tiempo Real</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔄 Actualizar Logs"):
            st.rerun()
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh (10s)")
    
    if auto_refresh:
        time.sleep(10)
        st.rerun()
    
    logs = controller.get_recent_logs(200)
    
    # Verificar si hay ejecución en progreso
    if 'bot_running' in st.session_state and st.session_state['bot_running']:
        execution_time = st.session_state.get('execution_time', datetime.now())
        elapsed = datetime.now() - execution_time
        st.info(f"🤖 Bot ejecutándose desde hace {elapsed.total_seconds():.0f} segundos")
        
        # Botón para marcar como completado manualmente
        if st.button("✅ Marcar como completado"):
            st.session_state['bot_running'] = False
    
    # Verificar archivo de última ejecución
    last_exec_file = controller.bot_path / "last_execution.log"
    if last_exec_file.exists():
        st.subheader("📋 Última Ejecución")
        with st.expander("Ver detalles de última ejecución"):
            try:
                with open(last_exec_file, 'r', encoding='utf-8') as f:
                    last_exec_content = f.read()
                st.code(last_exec_content)
            except Exception as e:
                st.error(f"Error leyendo archivo de ejecución: {e}")
    
    if logs:
        st.subheader(f"📋 Últimos {len(logs)} logs")
        
        # Filtros
        filter_text = st.text_input("🔍 Filtrar logs:", placeholder="Escribir para filtrar...")
        
        filtered_logs = logs
        if filter_text:
            filtered_logs = [log for log in logs if filter_text.lower() in log.lower()]
        
        # Mostrar logs en contenedor scrolleable
        logs_container = st.container()
        with logs_container:
            for i, log in enumerate(reversed(filtered_logs[-50:])):  # Últimos 50
                if '✅' in log or 'exitoso' in log.lower():
                    st.success(log.strip())
                elif '❌' in log or 'error' in log.lower():
                    st.error(log.strip())
                elif '⚠️' in log or 'warning' in log.lower():
                    st.warning(log.strip())
                else:
                    st.text(log.strip())
    else:
        st.info("📭 No hay logs disponibles")

# Página de Configuración
elif page == "🔧 Configuración":
    st.markdown('<h1 class="main-header">🔧 Configuración</h1>', unsafe_allow_html=True)
    
    st.subheader("📁 Gestión de Tiendas")
    
    tiendas = controller.get_available_tiendas()
    
    if tiendas:
        selected_tienda = st.selectbox("Seleccionar tienda para ver/editar:", tiendas)
        
        if selected_tienda:
            config = controller.load_tienda_config(selected_tienda)
            if config:
                st.subheader(f"⚙️ Configuración de {selected_tienda}")
                
                # Mostrar configuración en formato JSON editable
                config_json = st.text_area(
                    "Configuración JSON:",
                    value=json.dumps(config, indent=2, ensure_ascii=False),
                    height=400
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Guardar Cambios"):
                        try:
                            new_config = json.loads(config_json)
                            config_file = controller.tiendas_path / f"{selected_tienda}.json"
                            with open(config_file, 'w', encoding='utf-8') as f:
                                json.dump(new_config, f, indent=2, ensure_ascii=False)
                            st.success("✅ Configuración guardada exitosamente")
                        except json.JSONDecodeError as e:
                            st.error(f"❌ Error en JSON: {e}")
                        except Exception as e:
                            st.error(f"❌ Error guardando: {e}")
                
                with col2:
                    if st.button("🔄 Recargar Original"):
                        st.rerun()
    
    st.markdown("---")
    
    # Subir nueva configuración
    st.subheader("📤 Subir Nueva Tienda")
    uploaded_file = st.file_uploader("Subir archivo JSON:", type=['json'])
    
    if uploaded_file:
        try:
            config_data = json.load(uploaded_file)
            st.json(config_data)
            
            new_name = st.text_input("Nombre de la tienda:", value=uploaded_file.name.replace('.json', ''))
            
            if st.button("📥 Guardar Nueva Tienda"):
                config_file = controller.tiendas_path / f"{new_name}.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                st.success(f"✅ Tienda '{new_name}' guardada exitosamente")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error procesando archivo: {e}")

# Página de Screenshots
elif page == "📸 Screenshots":
    st.markdown('<h1 class="main-header">📸 Screenshots Recientes</h1>', unsafe_allow_html=True)
    
    screenshots = controller.get_screenshots()
    
    if screenshots:
        st.subheader(f"🖼️ Últimas {len(screenshots)} capturas")
        
        for screenshot in screenshots:
            with st.expander(f"📸 {screenshot['tienda']} - {screenshot['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    try:
                        st.image(str(screenshot['file']), caption=f"Captura de {screenshot['tienda']}")
                    except Exception as e:
                        st.error(f"Error cargando imagen: {e}")
                
                with col2:
                    st.info(f"""
                    📊 **Detalles:**
                    - 🏪 Tienda: {screenshot['tienda']}
                    - 📅 Fecha: {screenshot['timestamp'].strftime('%Y-%m-%d')}
                    - 🕒 Hora: {screenshot['timestamp'].strftime('%H:%M:%S')}
                    - 📏 Tamaño: {screenshot['size'] / 1024:.1f} KB
                    - 📁 Archivo: {screenshot['file'].name}
                    """)
                    
                    if st.button(f"📥 Descargar", key=f"download_{screenshot['file'].name}"):
                        with open(screenshot['file'], 'rb') as f:
                            st.download_button(
                                label="💾 Descargar Imagen",
                                data=f.read(),
                                file_name=screenshot['file'].name,
                                mime="image/png"
                            )
    else:
        st.info("📭 No hay screenshots disponibles")

# Información en sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Estado del Sistema")

# Estado en tiempo real en sidebar
stats = controller.get_statistics()
st.sidebar.metric("✅ Éxitos", stats['exitos'])
st.sidebar.metric("❌ Fallos", stats['fallos'])

if stats['last_execution']:
    st.sidebar.caption(f"🕒 Última: {stats['last_execution']}")

# Información del sistema
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Información")
st.sidebar.caption("🚀 Shopify Bot Dashboard")
st.sidebar.caption("📅 Versión 2.1 - Auto-Execute")
st.sidebar.caption("🔧 Streamlit UI")

# Auto-refresh para páginas que lo necesiten
if page in ["📊 Estadísticas", "📝 Logs en Vivo"]:
    time.sleep(1)  # Pequeña pausa para mejorar la experiencia
