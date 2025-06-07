"""
Log Viewer Module - Visualizador avanzado de logs
Navegación, filtrado y descarga de logs del sistema
"""

import streamlit as st
import os
import glob
from pathlib import Path
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional
import json

class LogViewer:
    """Visualizador de logs con funcionalidades avanzadas"""
    
    def __init__(self):
        self.logs_dir = Path(__file__).parent.parent / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Patrones para parsear logs
        self.log_patterns = {
            'timestamp': r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
            'level': r'(DEBUG|INFO|WARNING|ERROR|CRITICAL)',
            'order_id': r'Order ID[:\s]+([A-Za-z0-9]+)',
            'success': r'✅|ÉXITO|SUCCESS',
            'error': r'❌|ERROR|FALLO|FAIL',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'store_name': r'Tienda[:\s]+([A-Za-z0-9_-]+)',
        }
    
    def list_log_files(self) -> List[Dict]:
        """Listar todos los archivos de log con metadata"""
        log_files = []
        
        # Buscar archivos .log
        for log_path in self.logs_dir.glob("**/*.log"):
            try:
                stat = log_path.stat()
                log_files.append({
                    'name': log_path.name,
                    'path': str(log_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'relative_path': str(log_path.relative_to(self.logs_dir))
                })
            except Exception:
                continue
        
        # Ordenar por fecha de modificación (más reciente primero)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return log_files
    
    def read_log_file(self, file_path: str, max_lines: int = 1000) -> List[str]:
        """Leer archivo de log con límite de líneas"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
                # Limitar número de líneas para performance
                if len(lines) > max_lines:
                    return lines[-max_lines:]
                
                return lines
        except Exception as e:
            st.error(f"Error leyendo archivo: {e}")
            return []
    
    def parse_log_line(self, line: str) -> Dict:
        """Parsear una línea de log para extraer información"""
        parsed = {
            'raw': line.strip(),
            'timestamp': None,
            'level': 'INFO',
            'message': line.strip(),
            'has_order_id': False,
            'is_success': False,
            'is_error': False,
            'ip_addresses': [],
            'store_name': None
        }
        
        # Extraer timestamp
        timestamp_match = re.search(self.log_patterns['timestamp'], line)
        if timestamp_match:
            try:
                parsed['timestamp'] = datetime.strptime(
                    timestamp_match.group(1), 
                    '%Y-%m-%d %H:%M:%S'
                )
            except:
                pass
        
        # Extraer nivel de log
        level_match = re.search(self.log_patterns['level'], line)
        if level_match:
            parsed['level'] = level_match.group(1)
        
        # Detectar éxito/error
        parsed['is_success'] = bool(re.search(self.log_patterns['success'], line))
        parsed['is_error'] = bool(re.search(self.log_patterns['error'], line))
        
        # Extraer Order ID
        order_match = re.search(self.log_patterns['order_id'], line)
        if order_match:
            parsed['has_order_id'] = True
            parsed['order_id'] = order_match.group(1)
        
        # Extraer IPs
        ip_matches = re.findall(self.log_patterns['ip_address'], line)
        parsed['ip_addresses'] = list(set(ip_matches))
        
        # Extraer nombre de tienda
        store_match = re.search(self.log_patterns['store_name'], line)
        if store_match:
            parsed['store_name'] = store_match.group(1)
        
        return parsed
    
    def filter_logs(self, lines: List[str], filters: Dict) -> List[str]:
        """Filtrar líneas de log según criterios"""
        filtered_lines = []
        
        for line in lines:
            parsed = self.parse_log_line(line)
            
            # Aplicar filtros
            if filters.get('level') and filters['level'] != 'ALL':
                if parsed['level'] != filters['level']:
                    continue
            
            if filters.get('date_from'):
                if not parsed['timestamp'] or parsed['timestamp'].date() < filters['date_from']:
                    continue
            
            if filters.get('date_to'):
                if not parsed['timestamp'] or parsed['timestamp'].date() > filters['date_to']:
                    continue
            
            if filters.get('search_text'):
                if filters['search_text'].lower() not in line.lower():
                    continue
            
            if filters.get('only_success') and not parsed['is_success']:
                continue
            
            if filters.get('only_errors') and not parsed['is_error']:
                continue
            
            if filters.get('only_orders') and not parsed['has_order_id']:
                continue
            
            filtered_lines.append(line)
        
        return filtered_lines
    
    def get_execution_stats(self) -> Dict:
        """Obtener estadísticas de ejecuciones"""
        stats = {
            'total_executions': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'success_rate': 0,
            'unique_ips': set(),
            'stores_used': set(),
            'today_executions': 0,
            'last_execution': None
        }
        
        today = datetime.now().date()
        
        # Analizar todos los logs
        for log_file in self.list_log_files():
            lines = self.read_log_file(log_file['path'], max_lines=5000)
            
            for line in lines:
                parsed = self.parse_log_line(line)
                
                # Contar ejecuciones
                if 'PEDIDO:' in line or 'Order ID' in line:
                    stats['total_executions'] += 1
                    
                    # Ejecuciones de hoy
                    if parsed['timestamp'] and parsed['timestamp'].date() == today:
                        stats['today_executions'] += 1
                    
                    # Última ejecución
                    if parsed['timestamp']:
                        if not stats['last_execution'] or parsed['timestamp'] > stats['last_execution']:
                            stats['last_execution'] = parsed['timestamp']
                
                # Contar éxitos y fallos
                if parsed['is_success'] and parsed['has_order_id']:
                    stats['successful_orders'] += 1
                elif parsed['is_error'] and 'pedido' in line.lower():
                    stats['failed_orders'] += 1
                
                # Recopilar IPs y tiendas
                stats['unique_ips'].update(parsed['ip_addresses'])
                if parsed['store_name']:
                    stats['stores_used'].add(parsed['store_name'])
        
        # Calcular tasa de éxito
        total_orders = stats['successful_orders'] + stats['failed_orders']
        if total_orders > 0:
            stats['success_rate'] = (stats['successful_orders'] / total_orders) * 100
        
        # Convertir sets a conteos
        stats['unique_ips'] = len(stats['unique_ips'])
        stats['stores_used'] = len(stats['stores_used'])
        
        return stats
    
    def render_log_browser(self):
        """Renderizar navegador de archivos de log"""
        st.subheader("📁 Archivos de Log")
        
        log_files = self.list_log_files()
        
        if not log_files:
            st.info("📭 No hay archivos de log disponibles")
            return
        
        # Tabla de archivos
        for i, log_file in enumerate(log_files):
            with st.expander(f"📄 {log_file['name']} ({self.format_file_size(log_file['size'])})", expanded=i==0):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**Ruta:** {log_file['relative_path']}")
                    st.write(f"**Modificado:** {log_file['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Tamaño:** {self.format_file_size(log_file['size'])}")
                
                with col2:
                    if st.button("👁️ Ver", key=f"view_{i}"):
                        st.session_state.selected_log_file = log_file['path']
                        st.session_state.show_log_viewer = True
                
                with col3:
                    # Crear botón de descarga
                    try:
                        with open(log_file['path'], 'rb') as f:
                            file_data = f.read()
                        
                        st.download_button(
                            "📥 Descargar",
                            data=file_data,
                            file_name=log_file['name'],
                            mime="text/plain",
                            key=f"download_{i}"
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")
                
                with col4:
                    if st.button("🗑️ Eliminar", key=f"delete_{i}"):
                        if st.session_state.get(f'confirm_delete_log_{i}'):
                            try:
                                os.remove(log_file['path'])
                                st.success("✅ Archivo eliminado")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error eliminando: {e}")
                        else:
                            st.session_state[f'confirm_delete_log_{i}'] = True
                            st.warning("⚠️ Haz clic nuevamente para confirmar")
    
    def render_log_viewer(self, file_path: str):
        """Renderizar visor de contenido de log"""
        st.subheader(f"📖 Visualizando: {Path(file_path).name}")
        
        # Controles de filtrado
        with st.expander("🔍 Filtros de Búsqueda", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                level_filter = st.selectbox(
                    "Nivel de log",
                    options=['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    index=0
                )
                
                search_text = st.text_input(
                    "Buscar texto",
                    placeholder="Buscar en logs..."
                )
            
            with col2:
                date_from = st.date_input(
                    "Fecha desde",
                    value=datetime.now().date() - timedelta(days=7)
                )
                
                date_to = st.date_input(
                    "Fecha hasta",
                    value=datetime.now().date()
                )
            
            with col3:
                only_success = st.checkbox("Solo éxitos")
                only_errors = st.checkbox("Solo errores")
                only_orders = st.checkbox("Solo con Order ID")
                
                max_lines = st.slider(
                    "Máximo líneas",
                    min_value=100,
                    max_value=5000,
                    value=1000,
                    step=100
                )
        
        # Leer y filtrar logs
        with st.spinner("Cargando logs..."):
            lines = self.read_log_file(file_path, max_lines)
            
            if not lines:
                st.warning("📭 No hay contenido en el archivo")
                return
            
            # Aplicar filtros
            filters = {
                'level': level_filter,
                'date_from': date_from,
                'date_to': date_to,
                'search_text': search_text,
                'only_success': only_success,
                'only_errors': only_errors,
                'only_orders': only_orders
            }
            
            filtered_lines = self.filter_logs(lines, filters)
        
        # Estadísticas del archivo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📝 Total líneas", len(lines))
        
        with col2:
            st.metric("🔍 Filtradas", len(filtered_lines))
        
        with col3:
            success_count = sum(1 for line in filtered_lines if '✅' in line or 'ÉXITO' in line)
            st.metric("✅ Éxitos", success_count)
        
        with col4:
            error_count = sum(1 for line in filtered_lines if '❌' in line or 'ERROR' in line)
            st.metric("❌ Errores", error_count)
        
        st.divider()
        
        # Mostrar contenido
        st.subheader("📋 Contenido del Log")
        
        if not filtered_lines:
            st.info("🔍 No hay líneas que coincidan con los filtros")
            return
        
        # Renderizar líneas con colores
        log_container = st.container()
        
        with log_container:
            # CSS para estilos de log
            st.markdown("""
            <style>
            .log-line {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                margin: 1px 0;
                padding: 2px 5px;
                border-radius: 3px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .log-info { background-color: #e8f4f8; color: #0f5132; }
            .log-warning { background-color: #fff3cd; color: #664d03; }
            .log-error { background-color: #f8d7da; color: #721c24; }
            .log-success { background-color: #d1edff; color: #0a4275; }
            .log-debug { background-color: #f8f9fa; color: #495057; }
            </style>
            """, unsafe_allow_html=True)
            
            # Mostrar líneas (limitadas para performance)
            display_lines = filtered_lines[-500:] if len(filtered_lines) > 500 else filtered_lines
            
            for line in display_lines:
                parsed = self.parse_log_line(line)
                
                # Determinar clase CSS según contenido
                css_class = "log-info"
                if parsed['is_error'] or parsed['level'] == 'ERROR':
                    css_class = "log-error"
                elif parsed['is_success']:
                    css_class = "log-success" 
                elif parsed['level'] == 'WARNING':
                    css_class = "log-warning"
                elif parsed['level'] == 'DEBUG':
                    css_class = "log-debug"
                
                # Escapar HTML
                safe_line = line.replace('<', '&lt;').replace('>', '&gt;')
                
                st.markdown(
                    f'<div class="log-line {css_class}">{safe_line}</div>',
                    unsafe_allow_html=True
                )
            
            if len(filtered_lines) > 500:
                st.info(f"ℹ️ Mostrando las últimas 500 líneas de {len(filtered_lines)} total")
    
    def render_statistics(self):
        """Renderizar estadísticas de logs"""
        st.subheader("📊 Estadísticas de Ejecución")
        
        with st.spinner("Calculando estadísticas..."):
            stats = self.get_execution_stats()
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Total Ejecuciones", stats['total_executions'])
        
        with col2:
            st.metric(
                "✅ Pedidos Exitosos", 
                stats['successful_orders'],
                delta=f"{stats['success_rate']:.1f}%" if stats['success_rate'] > 0 else None
            )
        
        with col3:
            st.metric("❌ Pedidos Fallidos", stats['failed_orders'])
        
        with col4:
            st.metric("🌐 IPs Únicas", stats['unique_ips'])
        
        # Información adicional
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("🏪 Tiendas Usadas", stats['stores_used'])
            st.metric("📅 Ejecuciones Hoy", stats['today_executions'])
        
        with col2:
            if stats['last_execution']:
                last_exec_str = stats['last_execution'].strftime('%Y-%m-%d %H:%M:%S')
                st.metric("🕒 Última Ejecución", last_exec_str)
            else:
                st.metric("🕒 Última Ejecución", "N/A")
        
        # Gráfico de tasa de éxito
        if stats['successful_orders'] > 0 or stats['failed_orders'] > 0:
            st.subheader("📈 Distribución de Resultados")
            
            import pandas as pd
            
            chart_data = pd.DataFrame({
                'Resultado': ['Exitosos', 'Fallidos'],
                'Cantidad': [stats['successful_orders'], stats['failed_orders']]
            })
            
            st.bar_chart(chart_data.set_index('Resultado'))
    
    def format_file_size(self, size_bytes: int) -> str:
        """Formatear tamaño de archivo en formato legible"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
    
    def render(self):
        """Renderizar componente completo del visualizador de logs"""
        # Inicializar estado de sesión
        if 'show_log_viewer' not in st.session_state:
            st.session_state.show_log_viewer = False
        if 'selected_log_file' not in st.session_state:
            st.session_state.selected_log_file = None
        
        # Tabs principales
        tab1, tab2, tab3 = st.tabs(["📁 Archivos", "📖 Visor", "📊 Estadísticas"])
        
        with tab1:
            self.render_log_browser()
            
            # Acciones de mantenimiento
            st.divider()
            st.subheader("🧹 Mantenimiento")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🗑️ Limpiar Logs Antiguos", type="secondary"):
                    deleted_count = self.cleanup_old_logs(days=7)
                    st.success(f"✅ {deleted_count} archivos eliminados")
                    st.rerun()
            
            with col2:
                if st.button("📊 Generar Reporte"):
                    report = self.generate_summary_report()
                    st.download_button(
                        "📥 Descargar Reporte",
                        data=report,
                        file_name=f"reporte_logs_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )
            
            with col3:
                total_size = sum(f['size'] for f in self.list_log_files())
                st.metric("💾 Tamaño Total", self.format_file_size(total_size))
        
        with tab2:
            if st.session_state.show_log_viewer and st.session_state.selected_log_file:
                if st.button("← Volver a la lista"):
                    st.session_state.show_log_viewer = False
                    st.session_state.selected_log_file = None
                    st.rerun()
                
                st.divider()
                
                if os.path.exists(st.session_state.selected_log_file):
                    self.render_log_viewer(st.session_state.selected_log_file)
                else:
                    st.error("❌ El archivo seleccionado ya no existe")
                    st.session_state.show_log_viewer = False
            else:
                st.info("📋 Selecciona un archivo de log en la pestaña 'Archivos' para visualizarlo aquí")
        
        with tab3:
            self.render_statistics()
    
    def cleanup_old_logs(self, days: int = 7) -> int:
        """Limpiar logs antiguos"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for log_file in self.list_log_files():
            if log_file['modified'] < cutoff_date:
                try:
                    os.remove(log_file['path'])
                    deleted_count += 1
                except Exception:
                    continue
        
        return deleted_count
    
    def generate_summary_report(self) -> str:
        """Generar reporte resumen de logs"""
        stats = self.get_execution_stats()
        log_files = self.list_log_files()
        
        report = f"""# Reporte de Logs del Sistema
Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Estadísticas Generales
- Total de ejecuciones: {stats['total_executions']}
- Pedidos exitosos: {stats['successful_orders']}
- Pedidos fallidos: {stats['failed_orders']}
- Tasa de éxito: {stats['success_rate']:.1f}%
- IPs únicas utilizadas: {stats['unique_ips']}
- Tiendas utilizadas: {stats['stores_used']}
- Ejecuciones hoy: {stats['today_executions']}

## Archivos de Log
Total de archivos: {len(log_files)}
"""
        
        for log_file in log_files[:10]:  # Mostrar solo los 10 más recientes
            report += f"- {log_file['name']}: {self.format_file_size(log_file['size'])} ({log_file['modified'].strftime('%Y-%m-%d %H:%M')})\n"
        
        if len(log_files) > 10:
            report += f"... y {len(log_files) - 10} archivos más\n"
        
        report += f"\n## Resumen\n"
        if stats['last_execution']:
            report += f"Última ejecución: {stats['last_execution'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        total_size = sum(f['size'] for f in log_files)
        report += f"Tamaño total de logs: {self.format_file_size(total_size)}\n"
        
        return report
