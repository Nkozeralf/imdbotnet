import pandas as pd
import json
import os
import time
import logging
import subprocess
import threading
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from typing import Dict, List, Any
from PIL import Image

# ===== CONFIGURACIÓN =====
st.set_page_config(
    page_title="🛒 Sistema de Pedidos",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== IMPORTS DEL SISTEMA (SIN MODIFICAR) =====
import sys
sys.path.append('..')
try:
    from rotador_proxy import estado_proxies, obtener_proxy_colombiano_garantizado, test_all_systems
    from limpiador_logs import limpiar_logs
    from pedido_bot_base import cargar_configuracion_tienda, test_colombian_ip_validation
    from launcher import listar_tiendas, verificar_url_tienda, OptimizedOrderManager
    from dashboard_helpers import SystemInterface, LogAnalyzer, ConfigManager, NetworkTester, MaintenanceTools
    SISTEMA_DISPONIBLE = True
except ImportError as e:
    st.sidebar.error(f"⚠️ Error importando sistema: {e}")
    SISTEMA_DISPONIBLE = False

# ===== CONSTANTES =====
LOGS_DIR = "../logs"
TIENDAS_DIR = "../tiendas"
SCREENSHOTS_DIR = "../logs"

# ===== SERVICIOS CORE =====
class DashboardServices:
    """Servicios centralizados del dashboard"""
    
    @staticmethod
    @st.cache_data(ttl=30)
    def get_tiendas_list():
        """Obtener lista de tiendas con cache"""
        if not SISTEMA_DISPONIBLE:
            return []
        try:
            return listar_tiendas()
        except:
            return []
    
    @staticmethod
    @st.cache_data(ttl=60)
    def get_logs_data():
        """Cargar datos de logs con cache usando LogAnalyzer"""
        if not SISTEMA_DISPONIBLE:
            return {
                'pedidos_exitosos': [],
                'pedidos_fallidos': [],
                'screenshots': [],
                'stats': {}
            }
        
        try:
            # Usar LogAnalyzer para datos más detallados
            detailed_stats = LogAnalyzer.parse_real_time_logs()
            screenshots_by_store = LogAnalyzer.get_screenshots_by_store()
            
            # Aplanar screenshots
            all_screenshots = []
            for store_screenshots in screenshots_by_store.values():
                all_screenshots.extend(store_screenshots)
            
            return {
                'pedidos_exitosos': detailed_stats.get('pedidos_exitosos', []),
                'pedidos_fallidos': detailed_stats.get('pedidos_fallidos', []),
                'screenshots': all_screenshots,
                'screenshots_by_store': screenshots_by_store,
                'ips_utilizadas': detailed_stats.get('ips_utilizadas', []),
                'proxies_utilizados': detailed_stats.get('proxies_utilizados', []),
                'stats': detailed_stats
            }
        except Exception as e:
            return {
                'pedidos_exitosos': [],
                'pedidos_fallidos': [],
                'screenshots': [],
                'error': str(e)
            }
    
    @staticmethod
    def get_proxy_status():
        """Estado de proxies en tiempo real"""
        if not SISTEMA_DISPONIBLE:
            return {"error": "Sistema no disponible"}
        try:
            return estado_proxies()
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def test_proxy_connection():
        """Probar conexión proxy colombiano"""
        try:
            response = requests.get("http://proxy-svc:8002/health", timeout=5)
            return response.json() if response.status_code == 200 else {"status": "error"}
        except:
            return {"status": "error", "message": "Servicio no disponible"}

# ===== COMPONENTES UI =====
def render_sidebar():
    """Sidebar con controles principales"""
    st.sidebar.header("🎛️ Panel de Control")
    
    # Estado del sistema
    if SISTEMA_DISPONIBLE:
        st.sidebar.success("✅ Sistema Operativo")
    else:
        st.sidebar.error("❌ Sistema No Disponible")
    
    # Refresh automático
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)")
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Controles rápidos
    st.sidebar.subheader("⚡ Acciones Rápidas")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh", type="secondary"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("🗑️ Limpiar", type="secondary"):
            if SISTEMA_DISPONIBLE:
                try:
                    limpiar_logs(confirmado=True)
                    st.success("✅ Logs limpiados")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

def render_metrics_overview():
    """Métricas principales en overview"""
    logs_data = DashboardServices.get_logs_data()
    
    col1, col2, col3, col4 = st.columns(4)
    
    exitosos = len(logs_data['pedidos_exitosos'])
    fallidos = len(logs_data['pedidos_fallidos'])
    total = exitosos + fallidos
    tasa_exito = (exitosos / max(total, 1)) * 100
    
    with col1:
        st.metric("📦 Exitosos", exitosos, delta=f"+{exitosos}" if exitosos > 0 else None)
    
    with col2:
        st.metric("❌ Fallidos", fallidos, delta=f"+{fallidos}" if fallidos > 0 else None)
    
    with col3:
        st.metric("📈 Tasa Éxito", f"{tasa_exito:.1f}%")
    
    with col4:
        st.metric("🏪 Tiendas", len(DashboardServices.get_tiendas_list()))

def render_real_time_chart():
    """Gráfico en tiempo real de pedidos"""
    logs_data = DashboardServices.get_logs_data()
    
    if logs_data['pedidos_exitosos'] or logs_data['pedidos_fallidos']:
        # Crear datos para gráfico temporal
        exitosos_count = len(logs_data['pedidos_exitosos'])
        fallidos_count = len(logs_data['pedidos_fallidos'])
        
        # Gráfico de dona
        fig = go.Figure(data=[go.Pie(
            labels=['Exitosos', 'Fallidos'],
            values=[exitosos_count, fallidos_count],
            hole=0.4,
            marker_colors=['#28a745', '#dc3545']
        )])
        
        fig.update_layout(
            title="Estado de Pedidos en Tiempo Real",
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📝 No hay datos de pedidos disponibles")

def render_proxy_status():
    """Estado de proxies con información detallada"""
    proxy_status = DashboardServices.get_proxy_status()
    proxy_service_status = DashboardServices.test_proxy_connection()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🇨🇴 Proxy Colombiano")
        
        if proxy_service_status.get("status") == "ok":
            st.success("✅ Servicio Disponible")
            if "stats" in proxy_service_status:
                stats = proxy_service_status["stats"]
                st.metric("💽 GB Restantes", f"{stats.get('remaining_gb', 'N/A')}")
                st.metric("📈 Tasa Éxito", f"{stats.get('success_rate', 'N/A')}%")
        else:
            st.error("❌ Servicio No Disponible")
    
    with col2:
        st.subheader("🔄 DataImpulse Backup")
        
        if "error" not in proxy_status:
            dataimpulse_status = proxy_status.get("dataimpulse", {})
            if dataimpulse_status.get("available"):
                st.success("✅ DataImpulse OK")
                if dataimpulse_status.get("colombian_verified"):
                    st.success("🇨🇴 IP Colombiana Verificada")
                else:
                    st.warning("⚠️ IP no verificada")
            else:
                st.error("❌ DataImpulse no disponible")
        else:
            st.error(f"Error: {proxy_status['error']}")

def render_tiendas_manager():
    """Gestor de tiendas con CRUD básico"""
    st.subheader("🏪 Gestión de Tiendas")
    
    tiendas = DashboardServices.get_tiendas_list()
    
    if not tiendas:
        st.warning("📭 No hay tiendas configuradas")
        return
    
    # Lista de tiendas con acciones
    for tienda in tiendas:
        with st.expander(f"🏪 {tienda}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Mostrar configuración básica
                try:
                    if SISTEMA_DISPONIBLE:
                        config = cargar_configuracion_tienda(tienda)
                        st.write(f"**URL:** {config.get('url_producto', 'N/A')}")
                        st.write(f"**Mobile:** {'Sí' if config.get('emulate_mobile', False) else 'No'}")
                        st.write(f"**Popup:** {'Sí' if config.get('detecta_popup', False) else 'No'}")
                except:
                    st.error("❌ Error cargando configuración")
            
            with col2:
                if st.button(f"✅ Verificar", key=f"verify_{tienda}"):
                    if SISTEMA_DISPONIBLE:
                        try:
                            if verificar_url_tienda(tienda):
                                st.success("✅ Disponible")
                            else:
                                st.error("❌ No disponible")
                        except:
                            st.error("❌ Error verificando")
            
            with col3:
                if st.button(f"🗑️ Eliminar", key=f"delete_{tienda}"):
                    try:
                        tienda_path = os.path.join(TIENDAS_DIR, f"{tienda}.json")
                        if os.path.exists(tienda_path):
                            os.remove(tienda_path)
                            st.success(f"✅ {tienda} eliminada")
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

def render_screenshots_gallery():
    """Galería de screenshots con evidencias mejorada"""
    st.subheader("📸 Evidencias de Pedidos")
    
    logs_data = DashboardServices.get_logs_data()
    screenshots_by_store = logs_data.get('screenshots_by_store', {})
    
    if not screenshots_by_store:
        st.info("📭 No hay evidencias disponibles")
        return
    
    # Selector de tienda
    store_options = ["Todas las tiendas"] + list(screenshots_by_store.keys())
    selected_store = st.selectbox("Filtrar por tienda:", store_options)
    
    # Filtros adicionales
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Tipo:", ["Todos", "success", "error", "initial"])
    with col2:
        limit_images = st.slider("Mostrar últimas:", 5, 50, 20)
    with col3:
        if st.button("🗑️ Limpiar Antiguas"):
            try:
                result = MaintenanceTools.cleanup_old_files(days_old=7)
                if result["success"]:
                    st.success(f"✅ {result['deleted_count']} archivos eliminados")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Error: {result['error']}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Seleccionar screenshots a mostrar
    if selected_store == "Todas las tiendas":
        all_screenshots = []
        for store_screenshots in screenshots_by_store.values():
            all_screenshots.extend(store_screenshots)
        selected_screenshots = all_screenshots
    else:
        selected_screenshots = screenshots_by_store.get(selected_store, [])
    
    # Filtrar por tipo
    if filter_type != "Todos":
        selected_screenshots = [s for s in selected_screenshots if filter_type in s]
    
    # Limitar número de imágenes
    selected_screenshots = selected_screenshots[-limit_images:]
    
    if not selected_screenshots:
        st.info("📭 No hay evidencias que coincidan con los filtros")
        return
    
    # Mostrar información de almacenamiento
    disk_usage = MaintenanceTools.get_disk_usage("../logs")
    if disk_usage["success"]:
        st.info(f"💾 Uso de almacenamiento: {disk_usage['total_size_mb']:.1f} MB en {disk_usage['file_count']} archivos")
    
    # Galería organizada por tienda
    if selected_store == "Todas las tiendas":
        # Mostrar por tienda
        for store_name, store_screenshots in screenshots_by_store.items():
            if store_screenshots:
                with st.expander(f"🏪 {store_name} ({len(store_screenshots)} evidencias)"):
                    cols = st.columns(3)
                    for idx, screenshot_path in enumerate(store_screenshots[-6:]):  # Últimas 6 por tienda
                        with cols[idx % 3]:
                            try:
                                if os.path.exists(screenshot_path):
                                    image = Image.open(screenshot_path)
                                    st.image(image, caption=os.path.basename(screenshot_path), use_column_width=True)
                                    
                                    # Información del archivo
                                    file_stat = os.stat(screenshot_path)
                                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                                    file_size = file_stat.st_size / 1024  # KB
                                    
                                    st.caption(f"📅 {file_time.strftime('%H:%M:%S')} | 💾 {file_size:.1f} KB")
                                    
                                    if st.button(f"🗑️", key=f"del_img_{store_name}_{idx}"):
                                        os.remove(screenshot_path)
                                        st.success("✅ Eliminada")
                                        time.sleep(1)
                                        st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
    else:
        # Mostrar galería normal para tienda específica
        cols = st.columns(3)
        for idx, screenshot_path in enumerate(selected_screenshots):
            with cols[idx % 3]:
                try:
                    if os.path.exists(screenshot_path):
                        image = Image.open(screenshot_path)
                        st.image(image, caption=os.path.basename(screenshot_path), use_column_width=True)
                        
                        # Información detallada
                        file_stat = os.stat(screenshot_path)
                        file_time = datetime.fromtimestamp(file_stat.st_mtime)
                        file_size = file_stat.st_size / 1024
                        
                        st.caption(f"📅 {file_time.strftime('%H:%M:%S')} | 💾 {file_size:.1f} KB")
                        
                        if st.button(f"🗑️", key=f"del_img_single_{idx}"):
                            os.remove(screenshot_path)
                            st.success("✅ Eliminada")
                            time.sleep(1)
                            st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

def render_order_executor():
    """Ejecutor de pedidos integrado mejorado"""
    st.subheader("🚀 Ejecutor de Pedidos")
    
    if not SISTEMA_DISPONIBLE:
        st.error("❌ Sistema no disponible")
        return
    
    tiendas = DashboardServices.get_tiendas_list()
    if not tiendas:
        st.warning("📭 No hay tiendas configuradas")
        return
    
    # Configuración avanzada
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**⚙️ Configuración de Pedidos**")
        
        tiendas_seleccionadas = st.multiselect(
            "Seleccionar tiendas:",
            tiendas,
            default=[]
        )
        
        num_pedidos = st.slider("Pedidos por tienda:", 1, 5, 1)
        
        # Opciones avanzadas
        with st.expander("🔧 Opciones Avanzadas"):
            usar_proxy_service = st.checkbox("🇨🇴 Usar proxy colombiano", value=True)
            fast_mode = st.checkbox("⚡ Modo rápido (sin imágenes)", value=False)
            usar_intervalos = st.checkbox("⏱️ Intervalos aleatorios", value=True)
            
            # Pre-verificar tiendas
            if st.button("🔍 Pre-verificar Tiendas"):
                for tienda in tiendas_seleccionadas:
                    try:
                        if verificar_url_tienda(tienda):
                            st.success(f"✅ {tienda} - Disponible")
                        else:
                            st.error(f"❌ {tienda} - No disponible")
                    except:
                        st.error(f"❌ {tienda} - Error verificando")
    
    with col2:
        st.write("**📊 Resumen y Estado**")
        
        if tiendas_seleccionadas:
            total_pedidos = len(tiendas_seleccionadas) * num_pedidos
            
            # Estimación mejorada
            if usar_intervalos:
                tiempo_min = len(tiendas_seleccionadas) * 2
                tiempo_max = len(tiendas_seleccionadas) * 10
                tiempo_estimado = f"{tiempo_min}-{tiempo_max} minutos"
            else:
                tiempo_estimado = f"{total_pedidos * 2} minutos aprox."
            
            st.info(f"""
            **Resumen de Ejecución:**
            - 🏪 Tiendas: {len(tiendas_seleccionadas)}
            - 🔢 Pedidos por tienda: {num_pedidos}
            - 📦 Total pedidos: {total_pedidos}
            - 🇨🇴 Proxy service: {'Sí' if usar_proxy_service else 'No'}
            - ⚡ Modo rápido: {'Sí' if fast_mode else 'No'}
            - ⏱️ Intervalos: {'Sí' if usar_intervalos else 'No'}
            - 🕒 Tiempo estimado: {tiempo_estimado}
            """)
            
            # Estado del sistema
            proxy_status = DashboardServices.get_proxy_status()
            if "error" not in proxy_status:
                if proxy_status.get("proxy_service", {}).get("available"):
                    st.success("✅ Sistema proxy disponible")
                else:
                    st.warning("⚠️ Usando DataImpulse como backup")
            else:
                st.error("❌ Problemas con sistema proxy")
        else:
            st.write("📋 Selecciona tiendas para ver resumen")
    
    # Ejecución con método mejorado
    if st.button("🚀 EJECUTAR PEDIDOS", type="primary", disabled=not tiendas_seleccionadas):
        
        # Confirmación con detalles
        st.warning("⚠️ **CONFIRMACIÓN REQUERIDA**")
        st.write("Esto ejecutará pedidos REALES en las tiendas seleccionadas.")
        
        confirmacion = st.checkbox("✅ Confirmo que quiero ejecutar pedidos reales")
        
        if confirmacion:
            # Contenedores para UI en tiempo real
            progress_container = st.container()
            status_container = st.container()
            results_container = st.container()
            
            try:
                with status_container:
                    st.info("🚀 Iniciando ejecución usando el sistema optimizado...")
                
                # Usar SystemInterface para ejecutar sin modificar el sistema
                execution_params = {
                    "usar_proxy_service": usar_proxy_service,
                    "fast_mode": fast_mode,
                    "usar_intervalos": usar_intervalos
                }
                
                with progress_container:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Ejecutar usando subprocess (método no intrusivo)
                    with st.spinner("Ejecutando pedidos..."):
                        result = SystemInterface.execute_launcher_command(
                            tiendas_seleccionadas, 
                            num_pedidos, 
                            **execution_params
                        )
                    
                    progress_bar.progress(100)
                
                # Procesar resultados
                with results_container:
                    if result["success"]:
                        st.success("✅ Ejecución completada exitosamente")
                        
                        # Mostrar output relevante
                        output_lines = result["stdout"].split('\n')
                        success_lines = [line for line in output_lines if "✅ ÉXITO" in line]
                        error_lines = [line for line in output_lines if "❌ FALLO" in line]
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("✅ Exitosos", len(success_lines))
                        with col2:
                            st.metric("❌ Fallidos", len(error_lines))
                        with col3:
                            total = len(success_lines) + len(error_lines)
                            tasa = (len(success_lines) / max(total, 1)) * 100
                            st.metric("📈 Tasa Éxito", f"{tasa:.1f}%")
                        
                        # Mostrar detalles si hay resultados
                        if success_lines:
                            with st.expander("🎉 Pedidos Exitosos"):
                                for line in success_lines:
                                    st.success(line.strip())
                        
                        if error_lines:
                            with st.expander("💥 Pedidos Fallidos"):
                                for line in error_lines:
                                    st.error(line.strip())
                    
                    else:
                        st.error("❌ Error durante la ejecución")
                        if "error" in result:
                            st.error(f"Detalles: {result['error']}")
                        if result.get("stderr"):
                            with st.expander("📝 Detalles del Error"):
                                st.code(result["stderr"])
                
                # Actualizar cache para reflejar nuevos datos
                st.cache_data.clear()
                
            except Exception as e:
                st.error(f"❌ Error crítico durante la ejecución: {e}")
                st.exception(e)
        else:
            st.info("⚠️ Marca la confirmación para proceder con la ejecución")

def render_url_tester():
    """Probador de URLs con proxy"""
    st.subheader("🌐 Probador de URLs")
    
    url_to_test = st.text_input("URL a probar:", placeholder="https://ejemplo.com")
    
    col1, col2 = st.columns(2)
    
    with col1:
        use_proxy = st.checkbox("🇨🇴 Usar proxy colombiano", value=True)
    
    with col2:
        if st.button("🔍 Probar URL"):
            if url_to_test:
                with st.spinner("Probando conexión..."):
                    try:
                        if use_proxy and SISTEMA_DISPONIBLE:
                            # Obtener proxy colombiano
                            proxy = obtener_proxy_colombiano_garantizado("url_test")
                            if proxy:
                                st.success(f"✅ Proxy obtenido: {proxy.get('detected_ip', 'N/A')}")
                            else:
                                st.error("❌ No se pudo obtener proxy colombiano")
                                return
                        
                        # Probar URL (simulado - en realidad necesitarías usar Playwright)
                        response = requests.get(url_to_test, timeout=10)
                        
                        if response.status_code == 200:
                            st.success(f"✅ URL accesible - Código: {response.status_code}")
                            st.write(f"**Título:** {response.text[:100]}...")
                        else:
                            st.warning(f"⚠️ URL retornó código: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"❌ Error probando URL: {e}")
            else:
                st.warning("⚠️ Ingresa una URL válida")

# ===== APLICACIÓN PRINCIPAL =====
def main():
    # Header
    st.title("🛒 Sistema de Pedidos Automatizados")
    st.markdown("**Dashboard de Control y Monitoreo en Tiempo Real**")
    
    # Sidebar
    render_sidebar()
    
    # Métricas principales
    render_metrics_overview()
    st.divider()
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", 
        "🌐 Proxies", 
        "🏪 Tiendas",
        "📸 Evidencias",
        "🚀 Ejecutar",
        "🧪 Test URL"
    ])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            render_real_time_chart()
        with col2:
            render_proxy_status()
    
    with tab2:
        render_proxy_status()
        
        # Test de sistema completo
        if st.button("🧪 Test Sistema Completo"):
            with st.spinner("Probando sistema de proxies..."):
                if SISTEMA_DISPONIBLE:
                    try:
                        result = test_all_systems()
                        if result:
                            st.success("✅ Sistema de proxies funcionando correctamente")
                        else:
                            st.error("❌ Problemas en el sistema de proxies")
                    except Exception as e:
                        st.error(f"❌ Error en test: {e}")
    
    with tab3:
        render_tiendas_manager()
    
    with tab4:
        render_screenshots_gallery()
    
    with tab5:
        render_order_executor()
    
    with tab6:
        render_url_tester()
    
    # Footer con información
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"🕒 Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    
    with col2:
        st.caption("🔒 Flujo: VPN → Proxy CO → Navegación")
    
    with col3:
        if SISTEMA_DISPONIBLE:
            st.caption("✅ Sistema operativo")
        else:
            st.caption("❌ Sistema no disponible")

if __name__ == "__main__":
    main()

