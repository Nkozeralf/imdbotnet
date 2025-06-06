import os
import json
import time
import logging
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Set, Optional, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field

from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from rotador_proxy import probar_proxy
from pedido_bot_base import BrowserFingerprint, AntiDetection, LOG_DIR

# --- Logging ---
logger = logging.getLogger("web_security_analyzer")

@dataclass
class SecurityThreat:
    """Representa una amenaza/vulnerabilidad detectada"""
    name: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: float  # 0.0 - 1.0
    description: str
    evidence: List[str] = field(default_factory=list)
    attack_vectors: List[str] = field(default_factory=list)
    mitigation: str = ""

@dataclass
class AntiBotSystem:
    """Representa un sistema anti-bot detectado"""
    name: str
    confidence: float  # 0.0 - 1.0
    evidence: List[str] = field(default_factory=list)
    bypass_difficulty: str  # TRIVIAL, EASY, MEDIUM, HARD, EXTREME
    description: str = ""

class SecurityAnalyzer:
    """Analizador de seguridad web avanzado con detección precisa"""
    
    # Patrones más específicos y precisos
    ANTIBOT_SIGNATURES = {
        'cloudflare': {
            'patterns': [
                r'__cf_bm=[a-zA-Z0-9\-_.]+',
                r'cf_clearance=[a-zA-Z0-9\-_.]+',
                r'window\.__CF\$cv\$params',
                r'challenge-platform\.js',
                r'cf-browser-verification',
                r'Cloudflare Ray ID'
            ],
            'urls': [
                r'cdn-cgi/challenge-platform',
                r'cdnjs\.cloudflare\.com',
                r'challenges\.cloudflare\.com'
            ],
            'headers': ['cf-ray', 'cf-cache-status', 'server.*cloudflare'],
            'difficulty': 'HARD'
        },
        'incapsula': {
            'patterns': [
                r'incap_ses_[0-9]+_[0-9]+=[a-zA-Z0-9+/=]+',
                r'visid_incap_[0-9]+=[a-zA-Z0-9\-_.]+',
                r'incapsula\.js',
                r'imperva\.com'
            ],
            'urls': [r'[^/]*\.incapdns\.net', r'imperva\.com'],
            'headers': ['x-iinfo', 'x-cdn.*incapsula'],
            'difficulty': 'HARD'
        },
        'datadome': {
            'patterns': [
                r'datadome=[a-zA-Z0-9\-_.]+',
                r'dd_cookie_test_[a-zA-Z0-9]+',
                r'window\.DD_RUM',
                r'ddjskey=[a-zA-Z0-9]+'
            ],
            'urls': [r'js\.datadome\.co', r'geo\.captcha-delivery\.com'],
            'headers': ['x-dd-.*'],
            'difficulty': 'MEDIUM'
        },
        'perimeterx': {
            'patterns': [
                r'_px[2-6]=[a-zA-Z0-9\-_.]+',
                r'_pxvid=[a-zA-Z0-9\-_.]+',
                r'window\._px[A-Z]',
                r'perimeterx\.net'
            ],
            'urls': [r'client\.perimeterx\.net', r'collector-px[0-9]*\.perimeterx\.net'],
            'headers': ['x-px-.*'],
            'difficulty': 'MEDIUM'
        },
        'akamai': {
            'patterns': [
                r'_abck=[a-zA-Z0-9\-_.~]+',
                r'bm_sz=[a-zA-Z0-9\-_.]+',
                r'ak_bmsc=[a-zA-Z0-9\-_.]+',
                r'window\.bmak'
            ],
            'urls': [r'[^/]*\.akamaicdn\.net', r'[^/]*\.akamaized\.net'],
            'headers': ['x-akamai-.*'],
            'difficulty': 'EXTREME'
        },
        'recaptcha': {
            'patterns': [
                r'grecaptcha\.render',
                r'g-recaptcha',
                r'recaptcha/api\.js'
            ],
            'urls': [r'www\.google\.com/recaptcha', r'www\.gstatic\.com/recaptcha'],
            'headers': [],
            'difficulty': 'EASY'
        },
        'hcaptcha': {
            'patterns': [
                r'h-captcha',
                r'hcaptcha\.com/[0-9]+/api\.js'
            ],
            'urls': [r'hcaptcha\.com', r'assets\.hcaptcha\.com'],
            'headers': [],
            'difficulty': 'EASY'
        }
    }
    
    # Patrones de vulnerabilidades
    VULNERABILITY_PATTERNS = {
        'facebook_pixel': {
            'patterns': [
                r'fbq\s*\(\s*[\'"]init[\'"]',
                r'facebook\.net/.*fbevents\.js',
                r'connect\.facebook\.net/.*fbevents'
            ],
            'severity': 'MEDIUM',
            'description': 'Facebook Pixel detectado - tracking de usuarios'
        },
        'tiktok_pixel': {
            'patterns': [
                r'ttq\.track\s*\(',
                r'analytics\.tiktok\.com',
                r'tiktok_pixel'
            ],
            'severity': 'MEDIUM',
            'description': 'TikTok Pixel detectado - tracking de usuarios'
        },
        'google_analytics': {
            'patterns': [
                r'gtag\(.*UA-',
                r'google-analytics\.com/analytics\.js',
                r'googletagmanager\.com/gtag'
            ],
            'severity': 'LOW',
            'description': 'Google Analytics detectado - tracking básico'
        },
        'exposed_admin': {
            'patterns': [
                r'/admin[/?]',
                r'/administrator[/?]',
                r'/wp-admin[/?]',
                r'/cpanel[/?]'
            ],
            'severity': 'HIGH',
            'description': 'Rutas administrativas potencialmente expuestas'
        },
        'debug_info': {
            'patterns': [
                r'debug\s*=\s*true',
                r'console\.log\(',
                r'var_dump\(',
                r'print_r\('
            ],
            'severity': 'MEDIUM',
            'description': 'Información de debug expuesta'
        },
        'weak_csp': {
            'patterns': [
                r'unsafe-inline',
                r'unsafe-eval',
                r'\*\.amazonaws\.com'
            ],
            'severity': 'MEDIUM',
            'description': 'Content Security Policy débil'
        }
    }

    def __init__(self):
        self.detected_antibots: List[AntiBotSystem] = []
        self.detected_threats: List[SecurityThreat] = []
        self.page_content = ""
        self.response_headers = {}
        self.external_scripts = []
        
    def analyze_antibot_systems(self, content: str, scripts: List[str], headers: Dict[str, str]) -> List[AntiBotSystem]:
        """Detecta sistemas anti-bot con alta precisión"""
        detected = []
        
        for system_name, signatures in self.ANTIBOT_SIGNATURES.items():
            confidence = 0.0
            evidence = []
            
            # Verificar patrones en contenido
            content_matches = 0
            for pattern in signatures['patterns']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    content_matches += len(matches)
                    evidence.extend([f"Pattern '{pattern}': {match}" for match in matches[:3]])
            
            # Verificar URLs de scripts
            url_matches = 0
            for script in scripts:
                for url_pattern in signatures['urls']:
                    if re.search(url_pattern, script, re.IGNORECASE):
                        url_matches += 1
                        evidence.append(f"Script URL: {script}")
            
            # Verificar headers
            header_matches = 0
            for header_pattern in signatures['headers']:
                for header_name, header_value in headers.items():
                    if re.search(header_pattern, f"{header_name}: {header_value}", re.IGNORECASE):
                        header_matches += 1
                        evidence.append(f"Header: {header_name}: {header_value}")
            
            # Calcular confianza basada en múltiples indicadores
            if content_matches > 0:
                confidence += 0.4 + (content_matches * 0.1)
            if url_matches > 0:
                confidence += 0.3 + (url_matches * 0.05)
            if header_matches > 0:
                confidence += 0.3 + (header_matches * 0.05)
            
            # Solo reportar si hay confianza suficiente (reducir falsos positivos)
            if confidence >= 0.6:  # Umbral más alto
                detected.append(AntiBotSystem(
                    name=system_name.title(),
                    confidence=min(confidence, 1.0),
                    evidence=evidence,
                    bypass_difficulty=signatures['difficulty'],
                    description=f"Sistema {system_name.title()} confirmado con {len(evidence)} evidencias"
                ))
        
        return detected

    def analyze_vulnerabilities(self, content: str, scripts: List[str], headers: Dict[str, str]) -> List[SecurityThreat]:
        """Analiza vulnerabilidades y tracking"""
        threats = []
        
        for vuln_name, vuln_data in self.VULNERABILITY_PATTERNS.items():
            evidence = []
            confidence = 0.0
            
            # Buscar patrones
            for pattern in vuln_data['patterns']:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    evidence.extend([f"Pattern: {match}" for match in matches[:3]])
                    confidence += 0.3
            
            # Buscar en scripts
            for script in scripts:
                for pattern in vuln_data['patterns']:
                    if re.search(pattern, script, re.IGNORECASE):
                        evidence.append(f"Script: {script}")
                        confidence += 0.2
            
            if confidence > 0:
                # Definir vectores de ataque específicos
                attack_vectors = self._get_attack_vectors(vuln_name)
                mitigation = self._get_mitigation(vuln_name)
                
                threats.append(SecurityThreat(
                    name=vuln_name.replace('_', ' ').title(),
                    severity=vuln_data['severity'],
                    confidence=min(confidence, 1.0),
                    description=vuln_data['description'],
                    evidence=evidence,
                    attack_vectors=attack_vectors,
                    mitigation=mitigation
                ))
        
        return threats

    def _get_attack_vectors(self, vuln_type: str) -> List[str]:
        """Retorna vectores de ataque específicos para cada vulnerabilidad"""
        vectors = {
            'facebook_pixel': [
                'Extracción de datos de comportamiento del usuario',
                'Cross-site tracking',
                'Fingerprinting del navegador'
            ],
            'tiktok_pixel': [
                'Tracking de conversiones',
                'Perfilado de usuarios',
                'Compartir datos con terceros'
            ],
            'exposed_admin': [
                'Ataques de fuerza bruta',
                'Enumeración de usuarios',
                'Acceso no autorizado'
            ],
            'debug_info': [
                'Information disclosure',
                'Exposición de rutas internas',
                'Revelación de estructura de código'
            ],
            'weak_csp': [
                'XSS injection',
                'Code injection',
                'Clickjacking'
            ]
        }
        return vectors.get(vuln_type, ['Análisis manual requerido'])

    def _get_mitigation(self, vuln_type: str) -> str:
        """Retorna recomendaciones de mitigación"""
        mitigations = {
            'facebook_pixel': 'Implementar consentimiento de cookies, usar server-side tracking',
            'tiktok_pixel': 'Implementar consentimiento de cookies, limitar datos compartidos',
            'exposed_admin': 'Cambiar URLs por defecto, implementar IP whitelisting',
            'debug_info': 'Deshabilitar debug en producción, limpiar logs',
            'weak_csp': 'Implementar CSP estricto, eliminar unsafe-inline/unsafe-eval'
        }
        return mitigations.get(vuln_type, 'Consultar documentación de seguridad')

    def calculate_security_score(self) -> Tuple[int, str]:
        """Calcula score de seguridad de 1-100 con justificación"""
        base_score = 85  # Score base alto
        
        # Penalizaciones por anti-bot (positivo para seguridad)
        antibot_bonus = 0
        for antibot in self.detected_antibots:
            difficulty_scores = {'TRIVIAL': 1, 'EASY': 3, 'MEDIUM': 8, 'HARD': 15, 'EXTREME': 25}
            antibot_bonus += difficulty_scores.get(antibot.bypass_difficulty, 5) * antibot.confidence
        
        # Penalizaciones por vulnerabilidades
        vuln_penalty = 0
        severity_penalties = {'LOW': 3, 'MEDIUM': 8, 'HIGH': 15, 'CRITICAL': 25}
        
        for threat in self.detected_threats:
            penalty = severity_penalties.get(threat.severity, 5) * threat.confidence
            vuln_penalty += penalty
        
        # Calcular score final
        final_score = base_score + min(antibot_bonus, 15) - vuln_penalty
        final_score = max(1, min(100, int(final_score)))
        
        # Generar justificación
        justification = self._generate_score_justification(base_score, antibot_bonus, vuln_penalty, final_score)
        
        return final_score, justification

    def _generate_score_justification(self, base: int, bonus: float, penalty: float, final: int) -> str:
        """Genera justificación detallada del score"""
        parts = [f"Score base: {base}/100"]
        
        if bonus > 0:
            parts.append(f"Bonus por protecciones anti-bot: +{min(bonus, 15):.1f}")
        
        if penalty > 0:
            parts.append(f"Penalización por vulnerabilidades: -{penalty:.1f}")
        
        parts.append(f"Score final: {final}/100")
        
        # Clasificación
        if final >= 90:
            classification = "EXCELENTE - Muy alta seguridad"
        elif final >= 75:
            classification = "BUENA - Seguridad adecuada"
        elif final >= 50:
            classification = "REGULAR - Mejoras recomendadas"
        elif final >= 25:
            classification = "BAJA - Múltiples vulnerabilidades"
        else:
            classification = "CRÍTICA - Seguridad muy deficiente"
        
        return f"{' | '.join(parts)} | Clasificación: {classification}"

    def generate_security_report(self, store_id: str, url: str, analysis_time: float) -> Dict[str, Any]:
        """Genera reporte de seguridad estructurado como análisis de vulnerabilidades"""
        security_score, score_justification = self.calculate_security_score()
        
        # Organizar amenazas por severidad
        threats_by_severity = {}
        for threat in self.detected_threats:
            if threat.severity not in threats_by_severity:
                threats_by_severity[threat.severity] = []
            threats_by_severity[threat.severity].append({
                'name': threat.name,
                'confidence': f"{threat.confidence:.1%}",
                'description': threat.description,
                'evidence': threat.evidence,
                'attack_vectors': threat.attack_vectors,
                'mitigation': threat.mitigation
            })
        
        # Organizar sistemas anti-bot por dificultad
        antibots_by_difficulty = {}
        for antibot in self.detected_antibots:
            if antibot.bypass_difficulty not in antibots_by_difficulty:
                antibots_by_difficulty[antibot.bypass_difficulty] = []
            antibots_by_difficulty[antibot.bypass_difficulty].append({
                'name': antibot.name,
                'confidence': f"{antibot.confidence:.1%}",
                'description': antibot.description,
                'evidence': antibot.evidence
            })
        
        report = {
            # Información general
            'store_id': store_id,
            'target_url': url,
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_duration': f"{analysis_time:.2f}s",
            
            # Score de seguridad
            'security_assessment': {
                'overall_score': security_score,
                'score_explanation': score_justification,
                'risk_level': self._get_risk_level(security_score)
            },
            
            # Sistemas anti-bot detectados
            'anti_bot_protection': {
                'systems_detected': len(self.detected_antibots),
                'systems_by_difficulty': antibots_by_difficulty,
                'protection_summary': self._generate_protection_summary()
            },
            
            # Vulnerabilidades y amenazas
            'security_threats': {
                'total_threats': len(self.detected_threats),
                'threats_by_severity': threats_by_severity,
                'severity_breakdown': self._get_severity_breakdown()
            },
            
            # Recomendaciones
            'recommendations': self._generate_recommendations(),
            
            # Datos técnicos
            'technical_details': {
                'external_scripts_analyzed': len(self.external_scripts),
                'page_size': len(self.page_content),
                'response_headers_count': len(self.response_headers)
            }
        }
        
        return report

    def _get_risk_level(self, score: int) -> str:
        """Convierte score numérico a nivel de riesgo"""
        if score >= 90: return "VERY_LOW"
        elif score >= 75: return "LOW" 
        elif score >= 50: return "MEDIUM"
        elif score >= 25: return "HIGH"
        else: return "CRITICAL"

    def _generate_protection_summary(self) -> str:
        """Genera resumen de protecciones"""
        if not self.detected_antibots:
            return "No se detectaron sistemas de protección anti-bot significativos"
        
        extreme_count = sum(1 for ab in self.detected_antibots if ab.bypass_difficulty == 'EXTREME')
        hard_count = sum(1 for ab in self.detected_antibots if ab.bypass_difficulty == 'HARD')
        
        if extreme_count > 0:
            return f"Protección EXTREMA detectada ({extreme_count} sistemas críticos)"
        elif hard_count > 0:
            return f"Protección ALTA detectada ({hard_count} sistemas robustos)"
        else:
            return f"Protección BÁSICA detectada ({len(self.detected_antibots)} sistemas)"

    def _get_severity_breakdown(self) -> Dict[str, int]:
        """Cuenta amenazas por severidad"""
        breakdown = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for threat in self.detected_threats:
            breakdown[threat.severity] += 1
        return breakdown

    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en hallazgos"""
        recommendations = []
        
        # Recomendaciones por falta de protección
        if not self.detected_antibots:
            recommendations.append("CRÍTICO: Implementar sistema anti-bot (Cloudflare, Akamai, etc.)")
            recommendations.append("Configurar rate limiting y protección DDoS")
        
        # Recomendaciones por vulnerabilidades
        threat_types = [t.name.lower() for t in self.detected_threats]
        
        if any('pixel' in t for t in threat_types):
            recommendations.append("Implementar banner de consentimiento de cookies (GDPR/CCPA)")
            recommendations.append("Revisar políticas de privacidad y compartición de datos")
        
        if any('admin' in t for t in threat_types):
            recommendations.append("URGENTE: Ocultar/proteger rutas administrativas")
            recommendations.append("Implementar autenticación de dos factores")
        
        if any('debug' in t for t in threat_types):
            recommendations.append("Deshabilitar información de debug en producción")
        
        if not recommendations:
            recommendations.append("Mantener monitoreo continuo de seguridad")
            recommendations.append("Realizar auditorías de seguridad periódicas")
        
        return recommendations


def analizar_tienda(store_id: str, proxy_config: Dict[str, str], url_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Analizador de seguridad web mejorado con detección precisa y reportes estructurados
    
    Args:
        store_id: ID de la tienda o 'manual' para URL personalizada
        proxy_config: Configuración del proxy (obligatorio)
        url_override: URL personalizada para análisis manual
    """
    # Validar proxy
    if not proxy_config or not probar_proxy(proxy_config):
        raise RuntimeError("Proxy inválido - análisis requiere proxy funcional")

    # Determinar URL a analizar
    if url_override:
        url = url_override
        store_id = "manual_analysis"
        logger.info(f"🎯 Análisis manual de URL: {url}")
    else:
        # Cargar desde configuración
        cfg_path = f"tiendas/{store_id}.json"
        if not os.path.exists(cfg_path):
            raise RuntimeError(f"Configuración no encontrada: {cfg_path}")
        
        cfg = json.load(open(cfg_path, encoding="utf-8"))
        url = cfg.get("url_producto") or cfg.get("url")
        if not url:
            raise RuntimeError("URL no encontrada en configuración")

    # Inicializar analizador
    analyzer = SecurityAnalyzer()
    start_time = time.time()
    
    # Configurar Playwright
    pw = sync_playwright().start()
    
    try:
        logger.info(f"🔍 Iniciando análisis de seguridad: {store_id}")
        
        # Configurar browser con fingerprint
        fp = BrowserFingerprint.generate()
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage", 
                "--no-sandbox"
            ]
        )
        
        context = browser.new_context(
            user_agent=fp["user_agent"],
            viewport=fp["viewport"],
            proxy={
                "server": proxy_config["server"],
                "username": proxy_config["username"], 
                "password": proxy_config["password"]
            },
            ignore_https_errors=True,
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        )
        
        page = context.new_page()
        AntiDetection.apply(page)
        
        # Navegar con reintentos
        response = None
        for attempt in range(3):
            try:
                logger.info(f"Intento {attempt + 1}/3 - Navegando a {url}")
                response = page.goto(url, timeout=30000, wait_until='networkidle')
                logger.info(f"✅ Navegación exitosa - Status: {response.status}")
                break
            except Exception as e:
                logger.warning(f"❌ Intento {attempt + 1} falló: {str(e)[:100]}")
                if attempt == 2:
                    raise RuntimeError(f"Falló navegación después de 3 intentos: {e}")
                time.sleep(2)
        
        # Esperar carga completa
        time.sleep(3)
        
        # Recopilar datos
        analyzer.page_content = page.content()
        analyzer.response_headers = dict(response.headers) if response else {}
        
        # Obtener scripts externos
        script_elements = page.query_selector_all("script[src]")
        for element in script_elements:
            src = element.get_attribute("src")
            if src:
                # Convertir URLs relativas
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(url, src)
                analyzer.external_scripts.append(src)
        
        logger.info(f"📊 Datos recopilados: {len(analyzer.page_content)} chars, {len(analyzer.external_scripts)} scripts")
        
        # Realizar análisis
        analyzer.detected_antibots = analyzer.analyze_antibot_systems(
            analyzer.page_content, 
            analyzer.external_scripts, 
            analyzer.response_headers
        )
        
        analyzer.detected_threats = analyzer.analyze_vulnerabilities(
            analyzer.page_content,
            analyzer.external_scripts, 
            analyzer.response_headers
        )
        
        # Generar reporte
        analysis_time = time.time() - start_time
        report = analyzer.generate_security_report(store_id, url, analysis_time)
        
        # Logging de resultados
        score = report['security_assessment']['overall_score']
        antibots_count = report['anti_bot_protection']['systems_detected']
        threats_count = report['security_threats']['total_threats']
        
        logger.info(f"🎯 ANÁLISIS COMPLETADO:")
        logger.info(f"   📈 Score de Seguridad: {score}/100")
        logger.info(f"   🛡️  Sistemas Anti-bot: {antibots_count}")
        logger.info(f"   ⚠️  Amenazas detectadas: {threats_count}")
        
        if antibots_count > 0:
            for difficulty, systems in report['anti_bot_protection']['systems_by_difficulty'].items():
                logger.info(f"   - {difficulty}: {len(systems)} sistemas")
        
        if threats_count > 0:
            for severity, count in report['security_threats']['severity_breakdown'].items():
                if count > 0:
                    logger.warning(f"   - {severity}: {count} amenazas")
        
        # Guardar reporte
        output_dir = os.path.join(LOG_DIR, store_id)
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = int(time.time())
        report_file = os.path.join(output_dir, f"security_report_{timestamp}.json")
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Reporte guardado: {report_file}")
        
        return report
        
    except Exception as e:
        logger.error(f"💥 Error crítico en análisis: {e}")
        raise
        
    finally:
        # Cleanup
        try:
            if 'context' in locals():
                context.close()
            if 'browser' in locals(): 
                browser.close()
            pw.stop()
        except Exception as cleanup_error:
            logger.warning(f"Error en cleanup: {cleanup_error}")


# Función de conveniencia para análisis manual desde consola
def analizar_url(url: str, proxy_config: Dict[str, str]) -> Dict[str, Any]:
    """
    Función de conveniencia para analizar una URL específica desde consola
    
    Ejemplo:
        proxy = {"server": "http://proxy:port", "username": "user", "password": "pass"}
        resultado = analizar_url("https://ejemplo.com", proxy)
    """
    return analizar_tienda("manual", proxy_config, url_override=url)


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) > 1:
        url_to_analyze = sys.argv[1]
        proxy_example = {
            "server": "http://your-proxy:port",
            "username": "your-username", 
            "password": "your-password"
        }
        
        print(f"Analizando URL: {url_to_analyze}")
        print("Nota: Configurar proxy_config con credenciales reales")
        
        try:
            result = analizar_url(url_to_analyze, proxy_example)
            print(f"Score de seguridad: {result['security_assessment']['overall_score']}/100")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Uso: python analizador.py <URL>")
        print("Ejemplo: python analizador.py https://ejemplo.com")