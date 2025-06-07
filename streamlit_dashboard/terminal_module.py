"""Terminal Module - FUNCIONAL SIN ERRORES"""
import streamlit as st
import subprocess
import threading
import time
import os
from datetime import datetime

class TerminalComponent:
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        if 'terminal_process' not in st.session_state:
            st.session_state.terminal_process = None
        if 'terminal_output' not in st.session_state:
            st.session_state.terminal_output = []
        if 'terminal_active' not in st.session_state:
            st.session_state.terminal_active = False
    
    def add_output(self, text, output_type="stdout"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if text.strip():
            st.session_state.terminal_output.append({
                'timestamp': timestamp,
                'text': text.strip(),
                'type': output_type
            })
        if len(st.session_state.terminal_output) > 100:
            st.session_state.terminal_output = st.session_state.terminal_output[-100:]
    
    def start_bot_process(self):
        if st.session_state.terminal_active:
            return False
        
        try:
            cmd = [
                'bash', '-c', 
                'cd /home/botexecutor/shopify-bot && source /home/botexecutor/venv-playwright/bin/activate && python launcher.py'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            st.session_state.terminal_process = process
            st.session_state.terminal_active = True
            
            def read_output():
                while st.session_state.terminal_active:
                    if hasattr(st.session_state, 'terminal_process') and st.session_state.terminal_process:
                        if st.session_state.terminal_process.poll() is not None:
                            self.add_output("🔚 Proceso terminado", "system")
                            st.session_state.terminal_active = False
                            break
                        
                        try:
                            line = st.session_state.terminal_process.stdout.readline()
                            if line:
                                self.add_output(line.rstrip(), "stdout")
                            else:
                                time.sleep(0.1)
                        except:
                            break
                    else:
                        break
            
            threading.Thread(target=read_output, daemon=True).start()
            self.add_output("🚀 Bot iniciado exitosamente", "system")
            return True
            
        except Exception as e:
            self.add_output(f"❌ Error: {str(e)}", "error")
            return False
    
    def send_input(self, text):
        if not st.session_state.terminal_active or not st.session_state.terminal_process:
            return False
        
        try:
            st.session_state.terminal_process.stdin.write(text + '\n')
            st.session_state.terminal_process.stdin.flush()
            self.add_output(f">>> {text}", "input")
            return True
        except Exception as e:
            self.add_output(f"❌ Error enviando: {str(e)}", "error")
            return False
    
    def stop_bot_process(self):
        if not st.session_state.terminal_active:
            return
        
        try:
            if st.session_state.terminal_process:
                st.session_state.terminal_process.terminate()
            st.session_state.terminal_active = False
            self.add_output("🛑 Bot detenido", "system")
        except Exception as e:
            self.add_output(f"❌ Error deteniendo: {str(e)}", "error")
            st.session_state.terminal_active = False
    
    def render(self):
        # Controles
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.session_state.terminal_active:
                st.success("✅ Terminal Activo")
            else:
                st.info("💤 Terminal Inactivo")
        
        with col2:
            if st.button("🚀 Iniciar Bot", disabled=st.session_state.terminal_active):
                if self.start_bot_process():
                    time.sleep(1)
                    st.rerun()
        
        with col3:
            if st.button("🛑 Detener", disabled=not st.session_state.terminal_active):
                self.stop_bot_process()
                time.sleep(1)
                st.rerun()
        
        with col4:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        st.divider()
        
        # Salida del terminal
        st.subheader("📟 Salida del Terminal")
        
        terminal_html = '<div style="background-color:#1e1e1e;color:#ffffff;font-family:monospace;padding:15px;border-radius:8px;max-height:400px;overflow-y:auto;border:2px solid #333;">'
        
        for entry in st.session_state.terminal_output[-50:]:
            colors = {
                "stdout": "#e8e8e8",
                "input": "#4ecdc4", 
                "system": "#ffe66d",
                "error": "#ff6b6b"
            }
            color = colors.get(entry['type'], '#ffffff')
            text = entry['text'].replace('<', '&lt;').replace('>', '&gt;')
            terminal_html += f'<div style="color:{color};margin:3px 0;">[{entry["timestamp"]}] {text}</div>'
        
        if not st.session_state.terminal_output:
            terminal_html += '<div style="color:#ffe66d;font-style:italic;">🖥️ Terminal listo. Haz clic en "🚀 Iniciar Bot" para comenzar.</div>'
        
        terminal_html += '</div>'
        st.markdown(terminal_html, unsafe_allow_html=True)
        
        # Auto-refresh
        if st.session_state.terminal_active:
            time.sleep(2)
            st.rerun()
        
        # Entrada de comandos
        st.subheader("⌨️ Entrada de Comandos")
        
        with st.form("terminal_input", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input(
                    "Comando:",
                    placeholder="Escribe tu respuesta... (s, n, all, 1,2,3)",
                    disabled=not st.session_state.terminal_active,
                    label_visibility="collapsed"
                )
            
            with col2:
                send_btn = st.form_submit_button(
                    "📤 Enviar",
                    disabled=not st.session_state.terminal_active,
                    use_container_width=True
                )
            
            if send_btn and user_input.strip():
                if self.send_input(user_input):
                    time.sleep(0.5)
                    st.rerun()
        
        # Comandos rápidos
        st.subheader("⚡ Comandos Rápidos")
        
        col1, col2, col3, col4 = st.columns(4)
        commands = [
            ("s", "✅ Sí"),
            ("n", "❌ No"), 
            ("all", "🏪 Todas"),
            ("3", "3️⃣ Tres")
        ]
        
        for i, (cmd, desc) in enumerate(commands):
            with [col1, col2, col3, col4][i]:
                if st.button(
                    desc, 
                    disabled=not st.session_state.terminal_active,
                    use_container_width=True,
                    key=f"quick_{i}"
                ):
                    if self.send_input(cmd):
                        time.sleep(0.5)
                        st.rerun()
        
        # Segunda fila de comandos
        col1, col2, col3, col4 = st.columns(4)
        commands2 = [
            ("1", "1️⃣ Uno"),
            ("2", "2️⃣ Dos"),
            ("5", "5️⃣ Cinco"),
            ("1,2", "🔢 1,2")
        ]
        
        for i, (cmd, desc) in enumerate(commands2):
            with [col1, col2, col3, col4][i]:
                if st.button(
                    desc,
                    disabled=not st.session_state.terminal_active,
                    use_container_width=True,
                    key=f"quick2_{i}"
                ):
                    if self.send_input(cmd):
                        time.sleep(0.5)
                        st.rerun()
