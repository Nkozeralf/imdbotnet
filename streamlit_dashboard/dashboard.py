#!/usr/bin/env python3
"""
Dashboard Principal - Sistema de Pedidos Automatizados
Streamlit Dashboard moderno y responsivo
"""

import streamlit as st
import os
import sys
from pathlib import Path
import time
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="🛒 Shopify Bot Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Agregar path del proyecto principal
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importar módulos locales
from terminal_module import TerminalComponent
from crud_stores import StoreCRUD
from log_viewer import LogViewer
from styles import apply_custom_styles

# Aplicar estilos personalizados
apply_custom_styles()

# Estado de la aplicación
if 'terminal_active' not in st.session_state:
    st.session_state.terminal_active = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"

def render_header():
    """Renderizar header con información del sistema"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🛒 Shopify Bot Dashboard")
        st.caption("Sistema de Pedidos Automatizados - Control Completo")
    
    with col2:
        # Estado del sistema
        if os.path.exists("/tmp/bot_running.pid"):
            st.success("✅ Bot Activo")
        else:
            st.info("💤 Bot Inactivo")
    
    with col3:
        # Hora actual
        current_time = datetime.now().strftime("%H:%M:%S")
        st.metric("🕒 Hora", current_time)

def render_sidebar():
    """Sidebar con navegación principal"""
    st.sidebar.header("🎛️ Panel de Control")
    
    # Navegación principal
    pages = [
        "🏠 Dashboard",
        "💻 Terminal",
        "🏪 Tiendas", 
        "📋 Logs",
        "⚙️ Sistema"
    ]
    
    selected_page = st.sidebar.radio(
        "Navegación",
        pages,
        index=pages.index(st.session_state.current_page)
    )
    
    if selected_page != st.session_state.current_page:
        st.session_state.current_page = selected_page
        st.rerun()
    
    st.sidebar.divider()
    
    # Controles rápidos
    st.sidebar.subheader("⚡ Acciones Rápidas")
    
    if st.sidebar.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    if st.sidebar.button("🗑️ Limpiar Cache", use_container_width=True):
        st.cache_data.clear()
        st.sidebar.success("✅ Cache limpiado")
        time.sleep(1)
        st.rerun()
    
    # Estado del servidor
    st.sidebar.divider()
    st.sidebar.subheader("📊 Estado del Sistema")
    
    # CPU y memoria
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        st.sidebar.metric("🖥️ CPU", f"{cpu_percent:.1f}%")
        st.sidebar.metric("💾 RAM", f"{memory.percent:.1f}%")
        
        # Espacio en disco
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        st.sidebar.metric("💽 Disco", f"{disk_percent:.1f}%")
        
    except ImportError:
        st.sidebar.info("Instala psutil para métricas del sistema")

def render_dashboard_page():
    """Página principal del dashboard"""
    render_header()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    # Obtener estadísticas básicas
    try:
        from log_viewer import LogViewer
        log_viewer = LogViewer()
        stats = log_viewer.get_execution_stats()
        
        with col1:
            st.metric(
                "📦 Pedidos Totales", 
                stats.get('total_executions', 0),
                delta=stats.get('today_executions', 0)
            )
        
        with col2:
            success_rate = stats.get('success_rate', 0)
            st.metric(
                "✅ Tasa de Éxito",
                f"{success_rate:.1f}%",
                delta=f"{success_rate - 50:.1f}%" if success_rate != 0 else None
            )
        
        with col3:
            st.metric(
                "🏪 Tiendas",
                len(StoreCRUD.list_stores()),
                delta=None
            )
        
        with col4:
            st.metric(
                "📋 Logs",
                len(log_viewer.list_log_files()),
                delta=None
            )
    
    except Exception as e:
        st.error(f"Error cargando estadísticas: {e}")
    
    st.divider()
    
    # Gráficos y actividad reciente
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📈 Actividad Reciente")
        
        try:
            # Gráfico de actividad (simulado por ahora)
            import pandas as pd
            import numpy as np
            
            # Datos de ejemplo - en producción vendría de logs reales
            dates = pd.date_range(start='2025-06-01', end='2025-06-06', freq='D')
            data = {
                'Fecha': dates,
                'Exitosos': np.random.randint(10, 50, len(dates)),
                'Fallidos': np.random.randint(0, 10, len(dates))
            }
            df = pd.DataFrame(data)
            
            st.line_chart(
                df.set_index('Fecha')[['Exitosos', 'Fallidos']],
                height=300
            )
            
        except Exception as e:
            st.info("📊 Gráficos disponibles cuando haya más datos")
    
    with col_right:
        st.subheader("🔔 Estado del Sistema")
        
        # Verificar servicios críticos
        services_status = {
            "VPN Surfshark": check_vpn_status(),
            "Proxy Service": check_proxy_status(),
            "Bot Process": check_bot_status(),
            "Logs Directory": os.path.exists("../logs")
        }
        
        for service, status in services_status.items():
            if status:
                st.success(f"✅ {service}")
            else:
                st.error(f"❌ {service}")
        
        st.divider()
        
        # Botones de acción rápida
        st.subheader("⚡ Acciones Rápidas")
        
        if st.button("🚀 Ejecutar Bot", use_container_width=True, type="primary"):
            st.session_state.current_page = "💻 Terminal"
            st.rerun()
        
        if st.button("🏪 Gestionar Tiendas", use_container_width=True):
            st.session_state.current_page = "🏪 Tiendas"
            st.rerun()
        
        if st.button("📋 Ver Logs", use_container_width=True):
            st.session_state.current_page = "📋 Logs"
            st.rerun()

def render_terminal_page():
    """Página del terminal interactivo"""
    st.header("💻 Terminal Interactivo")
    st.caption("Ejecuta y controla el bot en tiempo real")
    
    # Componente terminal
    terminal = TerminalComponent()
    terminal.render()

def render_stores_page():
    """Página de gestión de tiendas"""
    st.header("🏪 Gestión de Tiendas")
    st.caption("Crear, editar y eliminar configuraciones de tiendas")
    
    # Componente CRUD de tiendas
    crud = StoreCRUD()
    crud.render()

def render_logs_page():
    """Página de visualización de logs"""
    st.header("📋 Visualizador de Logs")
    st.caption("Navegar, filtrar y descargar logs del sistema")
    
    # Componente visualizador de logs
    log_viewer = LogViewer()
    log_viewer.render()

def render_system_page():
    """Página de configuración del sistema"""
    st.header("⚙️ Configuración del Sistema")
    st.caption("Ajustes y mantenimiento del sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Mantenimiento")
        
        if st.button("🗑️ Limpiar Logs Antiguos", use_container_width=True):
            try:
                # Limpiar logs más antiguos de 7 días
                import glob
                from datetime import datetime, timedelta
                
                log_files = glob.glob("../logs/*.log")
                cutoff_date = datetime.now() - timedelta(days=7)
                deleted_count = 0
                
                for log_file in log_files:
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    if file_time < cutoff_date:
                        os.remove(log_file)
                        deleted_count += 1
                
                st.success(f"✅ {deleted_count} archivos eliminados")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        if st.button("🔄 Reiniciar Dashboard", use_container_width=True):
            st.warning("⚠️ Reiniciando dashboard...")
            time.sleep(2)
            st.rerun()
        
        if st.button("📊 Generar Reporte", use_container_width=True):
            try:
                # Generar reporte básico
                log_viewer = LogViewer()
                stats = log_viewer.get_execution_stats()
                
                report = f"""
# Reporte del Sistema - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Estadísticas Generales
- Total de ejecuciones: {stats.get('total_executions', 0)}
- Tasa de éxito: {stats.get('success_rate', 0):.1f}%
- Tiendas configuradas: {len(StoreCRUD.list_stores())}
- Archivos de log: {len(log_viewer.list_log_files())}

## Estado de Servicios
- VPN: {'✅ Activo' if check_vpn_status() else '❌ Inactivo'}
- Proxy: {'✅ Activo' if check_proxy_status() else '❌ Inactivo'}
- Bot: {'✅ Activo' if check_bot_status() else '❌ Inactivo'}
"""
                
                st.download_button(
                    "📥 Descargar Reporte",
                    report,
                    file_name=f"reporte_sistema_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"❌ Error generando reporte: {e}")
    
    with col2:
        st.subheader("📊 Información del Sistema")
        
        # Información del entorno
        st.code(f"""
Sistema Operativo: {os.name}
Python: {sys.version.split()[0]}
Directorio de trabajo: {os.getcwd()}
Usuario: {os.getenv('USER', 'desconocido')}
Streamlit: {st.__version__}
        """)
        
        # Variables de entorno relevantes
        st.subheader("🔐 Variables de Entorno")
        env_vars = ['PATH', 'PYTHONPATH', 'USER', 'HOME']
        for var in env_vars:
            value = os.getenv(var, 'No definida')
            if len(value) > 50:
                value = value[:47] + "..."
            st.text(f"{var}: {value}")

# Funciones auxiliares para verificar estado de servicios
def check_vpn_status() -> bool:
    """Verificar si VPN está activa"""
    try:
        # Verificar procesos de OpenVPN
        import subprocess
        result = subprocess.run(['pgrep', 'openvpn'], capture_output=True)
        return result.returncode == 0
    except:
        return False

def check_proxy_status() -> bool:
    """Verificar si el proxy service está disponible"""
    try:
        import requests
        response = requests.get("http://proxy-svc:8002/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_bot_status() -> bool:
    """Verificar si el bot está ejecutándose"""
    try:
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'launcher.py'], capture_output=True)
        return result.returncode == 0
    except:
        return False

# Función principal
def main():
    """Función principal de la aplicación"""
    render_sidebar()
    
    # Routing basado en la página seleccionada
    current_page = st.session_state.current_page
    
    if current_page == "🏠 Dashboard":
        render_dashboard_page()
    elif current_page == "💻 Terminal":
        render_terminal_page()
    elif current_page == "🏪 Tiendas":
        render_stores_page()
    elif current_page == "📋 Logs":
        render_logs_page()
    elif current_page == "⚙️ Sistema":
        render_system_page()
    else:
        st.error(f"Página no encontrada: {current_page}")
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"🕒 Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    
    with col2:
        st.caption("🛒 Shopify Bot Dashboard v2.0")
    
    with col3:
        st.caption("🔒 Seguro y Automatizado")

if __name__ == "__main__":
    main()
