"""
Styles Module - Estilos personalizados y temas para el dashboard
Incluye modo claro/oscuro y diseño responsivo
"""

import streamlit as st

def apply_custom_styles():
    """Aplicar estilos personalizados al dashboard"""
    
    # CSS personalizado
    custom_css = """
    <style>
    /* Variables de color para temas */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #ff7f0e;
        --error-color: #d62728;
        --info-color: #17a2b8;
        --background-color: #ffffff;
        --text-color: #000000;
        --border-color: #e1e5e9;
    }
    
    /* Tema oscuro */
    [data-theme="dark"] {
        --primary-color: #4dabf7;
        --secondary-color: #ffa94d;
        --success-color: #51cf66;
        --warning-color: #ffd43b;
        --error-color: #ff6b6b;
        --info-color: #74c0fc;
        --background-color: #0e1117;
        --text-color: #ffffff;
        --border-color: #30363d;
    }
    
    /* Estilos generales del dashboard */
    .main-header {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .metric-card {
        background-color: var(--background-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Estilos para botones */
    .stButton > button {
        border-radius: 6px;
        border: none;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Botón primario personalizado */
    .stButton > button[kind="primary"] {
        background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
        color: white;
    }
    
    /* Estilos para el sidebar */
    .css-1d391kg {
        background-color: var(--background-color);
        border-right: 1px solid var(--border-color);
    }
    
    /* Estilos para métricas */
    [data-testid="metric-container"] {
        background-color: var(--background-color);
        border: 1px solid var(--border-color);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Estilos para expanders */
    .streamlit-expanderHeader {
        background-color: var(--background-color);
        border: 1px solid var(--border-color);
        border-radius: 6px;
    }
    
    /* Terminal styles - ya definidos anteriormente */
    .terminal-output {
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: 'Courier New', 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
        font-size: 13px;
        line-height: 1.4;
        padding: 15px;
        border-radius: 8px;
        max-height: 500px;
        overflow-y: auto;
        border: 2px solid #333;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .terminal-line {
        margin: 3px 0;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .terminal-stdout { 
        color: #e8e8e8; 
    }
    
    .terminal-stderr { 
        color: #ff6b6b; 
        font-weight: bold;
    }
    
    .terminal-input { 
        color: #4ecdc4; 
        font-weight: bold;
        background-color: rgba(78, 205, 196, 0.1);
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    .terminal-system { 
        color: #ffe66d; 
        font-style: italic;
    }
    
    .terminal-error { 
        color: #ff6b6b; 
        font-weight: bold;
        background-color: rgba(255, 107, 107, 0.1);
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    /* Scrollbar personalizada para terminal */
    .terminal-output::-webkit-scrollbar {
        width: 8px;
    }
    
    .terminal-output::-webkit-scrollbar-track {
        background: #2d2d2d;
        border-radius: 4px;
    }
    
    .terminal-output::-webkit-scrollbar-thumb {
        background: #555;
        border-radius: 4px;
    }
    
    .terminal-output::-webkit-scrollbar-thumb:hover {
        background: #777;
    }
    
    /* Log viewer styles */
    .log-line {
        font-family: 'Courier New', 'SF Mono', 'Monaco', monospace;
        font-size: 12px;
        line-height: 1.3;
        margin: 1px 0;
        padding: 3px 8px;
        border-radius: 3px;
        white-space: pre-wrap;
        word-wrap: break-word;
        border-left: 3px solid transparent;
    }
    
    .log-info { 
        background-color: #e8f4f8; 
        color: #0f5132;
        border-left-color: #17a2b8;
    }
    
    .log-warning { 
        background-color: #fff3cd; 
        color: #664d03;
        border-left-color: #ffc107;
    }
    
    .log-error { 
        background-color: #f8d7da; 
        color: #721c24;
        border-left-color: #dc3545;
    }
    
    .log-success { 
        background-color: #d1edff; 
        color: #0a4275;
        border-left-color: #28a745;
    }
    
    .log-debug { 
        background-color: #f8f9fa; 
        color: #495057;
        border-left-color: #6c757d;
    }
    
    /* Tema oscuro para logs */
    [data-theme="dark"] .log-info { 
        background-color: rgba(23, 162, 184, 0.2); 
        color: #87ceeb;
    }
    
    [data-theme="dark"] .log-warning { 
        background-color: rgba(255, 193, 7, 0.2); 
        color: #ffd43b;
    }
    
    [data-theme="dark"] .log-error { 
        background-color: rgba(220, 53, 69, 0.2); 
        color: #ff6b6b;
    }
    
    [data-theme="dark"] .log-success { 
        background-color: rgba(40, 167, 69, 0.2); 
        color: #51cf66;
    }
    
    [data-theme="dark"] .log-debug { 
        background-color: rgba(108, 117, 125, 0.2); 
        color: #adb5bd;
    }
    
    /* Estilos para tablas */
    .dataframe {
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.9em;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .dataframe th {
        background-color: var(--primary-color);
        color: white;
        font-weight: bold;
        padding: 12px;
        text-align: left;
    }
    
    .dataframe td {
        padding: 10px 12px;
        border-bottom: 1px solid var(--border-color);
    }
    
    .dataframe tr:hover {
        background-color: rgba(31, 119, 180, 0.05);
    }
    
    /* Estilos responsivos */
    @media (max-width: 768px) {
        .main-header {
            padding: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .metric-card {
            margin-bottom: 0.5rem;
        }
        
        .terminal-output {
            font-size: 11px;
            max-height: 300px;
            padding: 10px;
        }
        
        .log-line {
            font-size: 11px;
            padding: 2px 6px;
        }
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.3s ease;
    }
    
    /* Estilos para status indicators */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-online {
        background-color: var(--success-color);
        box-shadow: 0 0 8px rgba(44, 160, 44, 0.6);
    }
    
    .status-offline {
        background-color: var(--error-color);
        box-shadow: 0 0 8px rgba(214, 39, 40, 0.6);
    }
    
    .status-warning {
        background-color: var(--warning-color);
        box-shadow: 0 0 8px rgba(255, 127, 14, 0.6);
    }
    
    /* Tooltips personalizados */
    .custom-tooltip {
        position: relative;
        cursor: help;
    }
    
    .custom-tooltip:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #333;
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 12px;
        white-space: nowrap;
        z-index: 1000;
    }
    
    /* Estilos para cards de información */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .success-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .warning-card {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .error-card {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        color: #721c24;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Estilos para el header principal */
    .dashboard-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .dashboard-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .dashboard-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Estilos para navegación */
    .nav-item {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        margin: 0.2rem 0;
        transition: all 0.2s ease;
    }
    
    .nav-item:hover {
        background-color: rgba(255,255,255,0.1);
        transform: translateX(5px);
    }
    
    .nav-item.active {
        background-color: rgba(255,255,255,0.2);
        border-left: 4px solid white;
    }
    
    /* Footer personalizado */
    .dashboard-footer {
        margin-top: 3rem;
        padding: 2rem;
        background-color: var(--background-color);
        border-top: 1px solid var(--border-color);
        text-align: center;
        color: var(--text-color);
        opacity: 0.7;
    }
    
    /* Estilos para formularios */
    .form-section {
        background-color: var(--background-color);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .form-section h3 {
        color: var(--primary-color);
        margin-top: 0;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 0.5rem;
    }
    
    /* Estilos para badges/etiquetas */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: bold;
        border-radius: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-success {
        background-color: var(--success-color);
        color: white;
    }
    
    .badge-warning {
        background-color: var(--warning-color);
        color: white;
    }
    
    .badge-error {
        background-color: var(--error-color);
        color: white;
    }
    
    .badge-info {
        background-color: var(--info-color);
        color: white;
    }
    
    /* Estilos para loading spinners */
    .loading-spinner {
        border: 3px solid #f3f3f3;
        border-top: 3px solid var(--primary-color);
        border-radius: 50%;
        width: 20px;
        height: 20px;
        animation: spin 1s linear infinite;
        display: inline-block;
        margin-right: 10px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Mejoras para selectbox y inputs */
    .stSelectbox > div > div {
        border-radius: 6px;
        border: 1px solid var(--border-color);
    }
    
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 1px solid var(--border-color);
    }
    
    /* Estilos para tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 0.5rem 1rem;
        background-color: var(--background-color);
        border: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Mostrar solo en modo desarrollo */
    .dev-info {
        display: none;
        position: fixed;
        bottom: 10px;
        right: 10px;
        background-color: rgba(0,0,0,0.8);
        color: white;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        z-index: 9999;
    }
    
    /* Estilos para códigos y pre */
    code {
        background-color: rgba(175, 184, 193, 0.2);
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    pre {
        background-color: #f8f9fa;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 1rem;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
    }
    
    [data-theme="dark"] pre {
        background-color: #2d3748;
        border-color: #4a5568;
        color: #e2e8f0;
    }
    
    /* Estilos para alertas personalizadas */
    .alert {
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    .alert-info {
        background-color: #e7f3ff;
        border-color: var(--info-color);
        color: #0c5460;
    }
    
    .alert-success {
        background-color: #e8f5e8;
        border-color: var(--success-color);
        color: #0f5132;
    }
    
    .alert-warning {
        background-color: #fff8e1;
        border-color: var(--warning-color);
        color: #664d03;
    }
    
    .alert-error {
        background-color: #ffeaea;
        border-color: var(--error-color);
        color: #721c24;
    }
    
    /* Modo oscuro para alertas */
    [data-theme="dark"] .alert-info {
        background-color: rgba(23, 162, 184, 0.2);
        color: #87ceeb;
    }
    
    [data-theme="dark"] .alert-success {
        background-color: rgba(40, 167, 69, 0.2);
        color: #51cf66;
    }
    
    [data-theme="dark"] .alert-warning {
        background-color: rgba(255, 193, 7, 0.2);
        color: #ffd43b;
    }
    
    [data-theme="dark"] .alert-error {
        background-color: rgba(220, 53, 69, 0.2);
        color: #ff6b6b;
    }
    
    /* Efectos de hover mejorados */
    .hover-lift {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .hover-lift:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Estilos para el modo móvil */
    @media (max-width: 480px) {
        .dashboard-header h1 {
            font-size: 1.8rem;
        }
        
        .dashboard-header p {
            font-size: 1rem;
        }
        
        .dashboard-header {
            padding: 1rem;
        }
        
        .metric-card {
            padding: 0.5rem;
        }
        
        .terminal-output {
            font-size: 10px;
            max-height: 250px;
            padding: 8px;
        }
        
        .log-line {
            font-size: 10px;
            padding: 1px 4px;
        }
        
        .form-section {
            padding: 1rem;
        }
    }
    
    /* Utilidades adicionales */
    .text-center { text-align: center; }
    .text-left { text-align: left; }
    .text-right { text-align: right; }
    
    .mt-1 { margin-top: 0.5rem; }
    .mt-2 { margin-top: 1rem; }
    .mt-3 { margin-top: 1.5rem; }
    
    .mb-1 { margin-bottom: 0.5rem; }
    .mb-2 { margin-bottom: 1rem; }
    .mb-3 { margin-bottom: 1.5rem; }
    
    .p-1 { padding: 0.5rem; }
    .p-2 { padding: 1rem; }
    .p-3 { padding: 1.5rem; }
    
    .rounded { border-radius: 6px; }
    .rounded-lg { border-radius: 12px; }
    
    .shadow-sm { box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .shadow { box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
    .shadow-lg { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    </style>
    """
    
    # Aplicar CSS
    st.markdown(custom_css, unsafe_allow_html=True)

def render_status_indicator(status: bool, online_text: str = "Online", offline_text: str = "Offline") -> str:
    """Renderizar indicador de estado con colores"""
    if status:
        return f'<span class="status-indicator status-online"></span>{online_text}'
    else:
        return f'<span class="status-indicator status-offline"></span>{offline_text}'

def render_badge(text: str, badge_type: str = "info") -> str:
    """Renderizar badge/etiqueta con estilo"""
    return f'<span class="badge badge-{badge_type}">{text}</span>'

def render_alert(message: str, alert_type: str = "info") -> str:
    """Renderizar alerta personalizada"""
    return f'<div class="alert alert-{alert_type}">{message}</div>'

def render_loading_spinner(text: str = "Cargando...") -> str:
    """Renderizar spinner de carga"""
    return f'<div><span class="loading-spinner"></span>{text}</div>'

def apply_theme_toggle():
    """Agregar toggle para cambiar entre tema claro y oscuro"""
    
    # Inicializar tema en session state
    if 'dark_theme' not in st.session_state:
        st.session_state.dark_theme = False
    
    # JavaScript para cambiar tema
    theme_js = """
    <script>
    function toggleTheme() {
        const body = document.body;
        const isDark = body.getAttribute('data-theme') === 'dark';
        
        if (isDark) {
            body.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        } else {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        }
    }
    
    // Cargar tema guardado
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    </script>
    """
    
    st.markdown(theme_js, unsafe_allow_html=True)

def get_responsive_columns(mobile_cols: int = 1, tablet_cols: int = 2, desktop_cols: int = 4):
    """Obtener configuración de columnas responsiva"""
    # En Streamlit, esto se simplifica a usar el número de columnas apropiado
    # En una implementación más avanzada, se podría usar JavaScript para detectar el tamaño de pantalla
    return desktop_cols  # Por simplicidad, usar columnas de escritorio

def create_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal") -> str:
    """Crear tarjeta de métrica personalizada"""
    delta_html = ""
    if delta:
        delta_class = f"delta-{delta_color}" if delta_color != "normal" else ""
        delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>'
    
    return f"""
    <div class="metric-card hover-lift">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

def create_info_box(title: str, content: str, box_type: str = "info") -> str:
    """Crear caja de información con estilo"""
    return f"""
    <div class="{box_type}-card">
        <h4>{title}</h4>
        <p>{content}</p>
    </div>
    """

# Funciones auxiliares para componentes comunes
def render_section_header(title: str, subtitle: str = None, icon: str = None):
    """Renderizar header de sección con estilo"""
    icon_html = f'<span class="section-icon">{icon}</span>' if icon else ''
    subtitle_html = f'<p class="section-subtitle">{subtitle}</p>' if subtitle else ''
    
    header_html = f"""
    <div class="section-header">
        {icon_html}
        <h2 class="section-title">{title}</h2>
        {subtitle_html}
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)

def render_divider_with_text(text: str):
    """Renderizar divisor con texto"""
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin: 2rem 0;">
        <div style="flex: 1; height: 1px; background-color: var(--border-color);"></div>
        <div style="padding: 0 1rem; color: var(--text-color); font-weight: 500;">{text}</div>
        <div style="flex: 1; height: 1px; background-color: var(--border-color);"></div>
    </div>
    """, unsafe_allow_html=True)

def add_custom_css_for_component(component_name: str, custom_css: str):
    """Agregar CSS personalizado para un componente específico"""
    css_with_scope = f"""
    <style>
    /* CSS para {component_name} */
    {custom_css}
    </style>
    """
    st.markdown(css_with_scope, unsafe_allow_html=True)

# Configuraciones predefinidas de estilo
TERMINAL_THEMES = {
    "dark": {
        "background": "#1e1e1e",
        "text": "#ffffff",
        "success": "#4ecdc4",
        "error": "#ff6b6b",
        "warning": "#ffe66d",
        "input": "#4ecdc4"
    },
    "light": {
        "background": "#f8f9fa",
        "text": "#000000",
        "success": "#28a745",
        "error": "#dc3545",
        "warning": "#ffc107",
        "input": "#007bff"
    },
    "matrix": {
        "background": "#000000",
        "text": "#00ff00",
        "success": "#00ff00",
        "error": "#ff0000",
        "warning": "#ffff00",
        "input": "#00ffff"
    }
}

def apply_terminal_theme(theme_name: str = "dark"):
    """Aplicar tema específico al terminal"""
    if theme_name not in TERMINAL_THEMES:
        theme_name = "dark"
    
    theme = TERMINAL_THEMES[theme_name]
    
    terminal_css = f"""
    <style>
    .terminal-output {{
        background-color: {theme['background']};
        color: {theme['text']};
    }}
    .terminal-stdout {{ color: {theme['text']}; }}
    .terminal-input {{ color: {theme['input']}; }}
    .terminal-success {{ color: {theme['success']}; }}
    .terminal-error {{ color: {theme['error']}; }}
    .terminal-warning {{ color: {theme['warning']}; }}
    </style>
    """
    
    st.markdown(terminal_css, unsafe_allow_html=True)
