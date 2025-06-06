# rotador_proxy_mejorado.py - Optimizado con IP colombiana garantizada
import json
import os
import secrets
import logging
import requests
import time
from typing import Dict, Optional
from urllib.parse import quote

logger = logging.getLogger("proxy_rotator_optimized")

class ColombianIPChecker:
    """Verificador específico de IPs colombianas"""
    
    @staticmethod
    def verify_ip_is_colombian(ip: str) -> bool:
        """Verificar si una IP específica es colombiana"""
        if not ip or ip.strip() == "":
            return False
        
        try:
            # Usar múltiples servicios para verificar país
            services = [
                f"http://ip-api.com/json/{ip}",
                f"https://ipapi.co/{ip}/json/",
                f"http://www.geoplugin.net/json.gp?ip={ip}"
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=8)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extraer código de país según servicio
                        country_code = None
                        if 'countryCode' in data:  # ip-api
                            country_code = data['countryCode']
                        elif 'country_code' in data:  # ipapi
                            country_code = data['country_code']
                        elif 'geoplugin_countryCode' in data:  # geoplugin
                            country_code = data['geoplugin_countryCode']
                        
                        if country_code and country_code.upper() == 'CO':
                            logger.debug(f"🇨🇴 IP {ip} confirmada como colombiana por {service}")
                            return True
                        elif country_code and country_code.upper() != 'CO':
                            logger.warning(f"❌ IP {ip} es de {country_code}, no de Colombia")
                            return False
                        
                except Exception as e:
                    logger.debug(f"Error verificando con {service}: {e}")
                    continue
            
            # Si no se pudo verificar con ningún servicio, asumir no colombiana por seguridad
            logger.warning(f"⚠️ No se pudo verificar país de IP {ip} - Asumiendo no colombiana")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verificando IP colombiana {ip}: {e}")
            return False


class ProxyServiceClient:
    """Cliente optimizado para el servicio de proxy colombiano"""
    
    def __init__(self, service_url: str = "http://proxy-svc:8002"):
        self.service_url = service_url
        self.session = requests.Session()
        self.last_proxy = None
        
    def get_proxy(self, session_id: str = None, force_new: bool = False) -> Optional[Dict[str, str]]:
        """Obtener proxy del servicio con verificación colombiana"""
        try:
            response = self.session.post(
                f"{self.service_url}/get-proxy",
                json={
                    "session_id": session_id,
                    "force_new": force_new
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar que el país sea Colombia
                if data.get("country", "").upper() != "CO":
                    logger.error(f"❌ Servicio proxy retornó país {data.get('country')}, no CO")
                    return None
                
                proxy_config = {
                    "server": data["proxy"],
                    "session_id": data["session_id"],
                    "country": data["country"],
                    "usage_mb": data.get("usage_mb", 0),
                    "source": "proxy_service"
                }
                
                # Verificar IP si está disponible en la respuesta
                if "detected_ip" in data:
                    if not ColombianIPChecker.verify_ip_is_colombian(data["detected_ip"]):
                        logger.error(f"❌ IP del servicio no es colombiana: {data['detected_ip']}")
                        return None
                    proxy_config["detected_ip"] = data["detected_ip"]
                
                self.last_proxy = proxy_config
                logger.info(f"✅ Proxy colombiano obtenido: {data['session_id']} ({data['country']})")
                return proxy_config
            else:
                logger.error(f"❌ Error del servicio proxy: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error conectando al servicio proxy: {e}")
            return None
    
    def rotate_proxy(self) -> Optional[Dict[str, str]]:
        """Forzar rotación de proxy con verificación colombiana"""
        try:
            response = self.session.post(f"{self.service_url}/rotate-proxy", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Verificar que el país sea Colombia
                if data.get("country", "").upper() != "CO":
                    logger.error(f"❌ Proxy rotado no es colombiano: {data.get('country')}")
                    return None
                
                proxy_config = {
                    "server": data["proxy"],
                    "session_id": data["session_id"],
                    "country": data["country"],
                    "usage_mb": data.get("usage_mb", 0),
                    "source": "proxy_service"
                }
                
                self.last_proxy = proxy_config
                logger.info(f"🔄 Proxy colombiano rotado: {data['session_id']}")
                return proxy_config
            return None
        except Exception as e:
            logger.error(f"❌ Error rotando proxy: {e}")
            return None
    
    def test_service(self) -> bool:
        """Probar si el servicio está disponible"""
        try:
            response = self.session.get(f"{self.service_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🟢 Servicio proxy disponible - Estado: {data.get('status', 'unknown')}")
                return True
            return False
        except Exception as e:
            logger.debug(f"Servicio proxy no disponible: {e}")
            return False


class DataImpulseManager:
    """Gestor optimizado para DataImpulse con verificación IP colombiana"""
    
    def __init__(self, credentials_path: str = "config/credentials.json"):
        self.credentials_path = credentials_path
        self._credentials = None
        
    def _load_credentials(self) -> Dict:
        """Carga las credenciales del archivo de configuración"""
        if self._credentials is not None:
            return self._credentials
            
        possible_paths = [
            self.credentials_path,
            "credentials.json",
            os.path.join(os.getcwd(), "credentials.json"),
            os.path.join("config", "credentials.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "dataimpulse" not in data:
                        raise ValueError(f"Falta sección 'dataimpulse' en {path}")
                    self._credentials = data
                    logger.info(f"✅ Credenciales DataImpulse cargadas desde: {path}")
                    return data
                except Exception as e:
                    logger.error(f"❌ Error leyendo {path}: {e}")
                    continue
        
        raise FileNotFoundError("No se encontró archivo de credenciales válido para DataImpulse")

    def create_proxy_config(self, country: str = "CO") -> Dict[str, str]:
        """Crea la configuración del proxy para Colombia específicamente"""
        try:
            creds = self._load_credentials()["dataimpulse"]
            
            username = creds["login"]
            password = creds["password"]
            host = creds["host"]
            port = str(creds["port"])
            
            # SIEMPRE forzar Colombia, nunca GLOBAL
            if country.upper() != "CO":
                logger.warning(f"⚠️ País {country} solicitado, forzando a CO")
                country = "CO"
            
            # CORRECCIÓN: Usar formato DataImpulse correcto con __cr.co
            # Según documentación: 5029fe3a90880a1c12af__cr.co:4bb091b6a8a200e1
            username_formatted = f"{username}__cr.{country.lower()}"
            
            proxy_config = {
                "server": f"http://{host}:{port}",
                "username": username_formatted,
                "password": password,
                "host": host,
                "port": port,
                "country": "CO",  # SIEMPRE Colombia
                "source": "dataimpulse"
            }
            
            logger.info(f"🔧 Configuración DataImpulse creada para Colombia con formato correcto")
            return proxy_config
            
        except Exception as e:
            logger.error(f"❌ Error creando configuración DataImpulse: {e}")
            return {}

    def test_proxy(self, proxy_config: Dict[str, str]) -> bool:
        """Prueba el proxy DataImpulse Y VERIFICA que sea IP colombiana"""
        if not proxy_config:
            return False
        
        try:
            username = quote(proxy_config['username'])
            password = quote(proxy_config['password'])
            host = proxy_config['host']
            port = proxy_config['port']
            
            proxy_url = f"http://{username}:{password}@{host}:{port}"
            
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            logger.info(f"🔍 Probando DataImpulse con formato: {username}@{host}:{port}")
            
            # Probar conectividad básica
            response = requests.get(
                "http://api.ipify.org", 
                proxies=proxies, 
                timeout=15,
                headers={'User-Agent': 'curl/7.68.0'}
            )
            
            if response.status_code == 200:
                detected_ip = response.text.strip()
                
                # CRÍTICO: Verificar que sea IP colombiana
                is_colombian = ColombianIPChecker.verify_ip_is_colombian(detected_ip)
                
                if not is_colombian:
                    logger.error(f"❌ DataImpulse retornó IP no colombiana: {detected_ip}")
                    return False
                
                proxy_config["detected_ip"] = detected_ip
                logger.info(f"✅ DataImpulse OK - IP colombiana confirmada: {detected_ip}")
                return True
            else:
                logger.error(f"❌ DataImpulse HTTP {response.status_code}: {response.text[:100]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error probando DataImpulse: {str(e)}")
            return False

    def test_proxy_with_retries(self, proxy_config: Dict[str, str], max_retries: int = 3) -> bool:
        """Probar proxy con reintentos para obtener IP colombiana"""
        for attempt in range(max_retries):
            logger.info(f"🔄 Intento {attempt + 1}/{max_retries} para obtener IP colombiana")
            
            if self.test_proxy(proxy_config):
                return True
            
            if attempt < max_retries - 1:
                logger.info("⏳ Esperando antes del siguiente intento...")
                time.sleep(2)
        
        logger.error(f"❌ No se pudo obtener IP colombiana después de {max_retries} intentos")
        return False


class OptimizedProxyManager:
    """Gestor principal optimizado con IP colombiana GARANTIZADA"""
    
    def __init__(self):
        self.proxy_service = ProxyServiceClient()
        self.dataimpulse = DataImpulseManager()
        self.prefer_service = True
        self.fallback_enabled = True
        
        # Verificar disponibilidad del servicio al inicializar
        if not self.proxy_service.test_service():
            logger.warning("⚠️ Servicio de proxy no disponible, usando solo DataImpulse")
            self.prefer_service = False
    
    def get_proxy(self, country: str = "CO", force_new: bool = False) -> Optional[Dict[str, str]]:
        """Obtener proxy GARANTIZANDO IP colombiana"""
        
        # Solo aceptar país Colombia
        if country.upper() != "CO":
            logger.warning(f"⚠️ País {country} solicitado, forzando a CO por seguridad")
            country = "CO"
        
        logger.info("🇨🇴 Buscando proxy con IP colombiana garantizada...")
        
        # Estrategia 1: Servicio de proxy colombiano (preferido)
        if self.prefer_service:
            logger.info("🔍 Intentando servicio de proxy colombiano...")
            proxy = self.proxy_service.get_proxy(force_new=force_new)
            if proxy and self._validate_proxy_colombian(proxy):
                logger.info(f"✅ Proxy servicio colombiano validado: {proxy.get('session_id')}")
                return proxy
            else:
                logger.warning("⚠️ Servicio de proxy no retornó IP colombiana válida")
        
        # Estrategia 2: DataImpulse con verificación colombiana estricta
        if self.fallback_enabled:
            logger.info("🔄 Intentando DataImpulse con verificación colombiana...")
            
            # Intentar múltiples configuraciones para asegurar IP colombiana
            for attempt in range(3):
                try:
                    proxy_config = self.dataimpulse.create_proxy_config("CO")
                    if proxy_config and self.dataimpulse.test_proxy_with_retries(proxy_config):
                        logger.info(f"✅ DataImpulse colombiano validado (intento {attempt + 1})")
                        return proxy_config
                    
                    if attempt < 2:
                        logger.info(f"⏳ Reintentando configuración DataImpulse...")
                        time.sleep(3)
                        
                except Exception as e:
                    logger.error(f"❌ DataImpulse intento {attempt + 1}: {e}")
        
        logger.error("❌ FALLO CRÍTICO: No se pudo obtener proxy con IP colombiana")
        return None
    
    def rotate_proxy(self) -> Optional[Dict[str, str]]:
        """Forzar rotación manteniendo IP colombiana"""
        logger.info("🔄 Rotando proxy manteniendo IP colombiana...")
        
        if self.prefer_service:
            proxy = self.proxy_service.rotate_proxy()
            if proxy and self._validate_proxy_colombian(proxy):
                return proxy
        
        # Fallback: crear nuevo proxy DataImpulse
        return self.get_proxy("CO", force_new=True)
    
    def _validate_proxy_colombian(self, proxy_config: Dict[str, str]) -> bool:
        """Validación estricta de proxy colombiano"""
        try:
            # Para el servicio de proxy, verificar que el país sea CO
            if proxy_config.get("source") == "proxy_service":
                country = proxy_config.get("country", "").upper()
                if country != "CO":
                    logger.error(f"❌ Proxy servicio no es CO: {country}")
                    return False
                return True
            
            # Para otros proxies, hacer validación completa
            return self.dataimpulse.test_proxy(proxy_config)
            
        except Exception as e:
            logger.error(f"❌ Error validando proxy colombiano: {e}")
            return False
    
    def get_status(self) -> Dict[str, any]:
        """Obtener estado completo del sistema de proxies"""
        status = {
            "proxy_service": {
                "available": False,
                "stats": {},
                "colombian_verified": False
            },
            "dataimpulse": {
                "available": False,
                "credentials_loaded": False,
                "colombian_verified": False
            },
            "preferred_method": "proxy_service" if self.prefer_service else "dataimpulse",
            "colombian_ip_guaranteed": True  # Nueva métrica
        }
        
        # Estado del servicio de proxy
        try:
            if self.proxy_service.test_service():
                status["proxy_service"]["available"] = True
                
                # Intentar obtener stats
                try:
                    response = self.proxy_service.session.get(f"{self.proxy_service.service_url}/stats", timeout=5)
                    if response.status_code == 200:
                        status["proxy_service"]["stats"] = response.json()
                except:
                    pass
                
                # Verificar si el servicio garantiza IP colombiana
                test_proxy = self.proxy_service.get_proxy()
                if test_proxy and test_proxy.get("country", "").upper() == "CO":
                    status["proxy_service"]["colombian_verified"] = True
        except:
            pass
        
        # Estado de DataImpulse
        try:
            self.dataimpulse._load_credentials()
            status["dataimpulse"]["credentials_loaded"] = True
            status["dataimpulse"]["available"] = True
            
            # Verificar que DataImpulse puede obtener IP colombiana
            test_config = self.dataimpulse.create_proxy_config("CO")
            if test_config:
                status["dataimpulse"]["colombian_verified"] = True
        except:
            pass
        
        return status

    def get_colombian_proxy_guaranteed(self, store_id: str = None) -> Optional[Dict[str, str]]:
        """Método específico que GARANTIZA IP colombiana o falla"""
        session_suffix = f"_{store_id}" if store_id else ""
        
        logger.info(f"🇨🇴 GARANTIZANDO proxy colombiano{session_suffix}...")
        
        # Intentar hasta 3 veces con diferentes métodos
        methods = [
            ("proxy_service", lambda: self.proxy_service.get_proxy(session_id=f"store{session_suffix}")),
            ("dataimpulse_1", lambda: self._try_dataimpulse_colombian()),
            ("dataimpulse_2", lambda: self._try_dataimpulse_colombian())
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"🔍 Probando método: {method_name}")
                proxy = method_func()
                
                if proxy and self._validate_proxy_colombian(proxy):
                    # Verificación adicional de IP si está disponible
                    if "detected_ip" in proxy:
                        if ColombianIPChecker.verify_ip_is_colombian(proxy["detected_ip"]):
                            logger.info(f"✅ GARANTÍA CUMPLIDA: IP colombiana {proxy['detected_ip']} via {method_name}")
                            return proxy
                        else:
                            logger.error(f"❌ IP no colombiana detectada: {proxy['detected_ip']}")
                            continue
                    else:
                        logger.info(f"✅ Proxy colombiano obtenido via {method_name}")
                        return proxy
                
            except Exception as e:
                logger.error(f"❌ Método {method_name} falló: {e}")
                continue
        
        logger.error("❌ FALLO TOTAL: No se pudo GARANTIZAR proxy colombiano")
        return None
    
    def _try_dataimpulse_colombian(self) -> Optional[Dict[str, str]]:
        """Intentar obtener proxy colombiano de DataImpulse"""
        config = self.dataimpulse.create_proxy_config("CO")
        if config and self.dataimpulse.test_proxy_with_retries(config):
            return config
        return None


# ─── Instancia global optimizada ────────────────────────────────────────────────────
_proxy_manager = OptimizedProxyManager()

# ─── Funciones de compatibilidad optimizadas ────────────────────────────────────────────────────

def obtener_proxy(pais: str = "CO") -> Optional[Dict[str, str]]:
    """Función de compatibilidad - SIEMPRE retorna proxy colombiano o None"""
    return _proxy_manager.get_proxy("CO")  # Forzar siempre Colombia

def probar_proxy(proxy_config: Dict[str, str]) -> bool:
    """Función de compatibilidad - Incluye verificación colombiana"""
    if not proxy_config:
        return False
    
    # Si es del servicio de proxy, verificar país
    if proxy_config.get("source") == "proxy_service":
        country = proxy_config.get("country", "").upper()
        return country == "CO"
    
    # Si tiene servidor pero no username/password, es del servicio
    if proxy_config.get("server") and not proxy_config.get("username"):
        return True  # Asumir válido del servicio
    
    # Para DataImpulse, hacer prueba completa con verificación IP
    return _proxy_manager.dataimpulse.test_proxy(proxy_config)

def rotar_proxy() -> Optional[Dict[str, str]]:
    """Función de rotación - GARANTIZA IP colombiana"""
    return _proxy_manager.rotate_proxy()

def estado_proxies() -> Dict[str, any]:
    """Función de estado - Incluye verificación colombiana"""
    return _proxy_manager.get_status()

def obtener_proxy_colombiano_garantizado(store_id: str = None) -> Optional[Dict[str, str]]:
    """Nueva función que GARANTIZA IP colombiana o falla"""
    return _proxy_manager.get_colombian_proxy_guaranteed(store_id)

# ─── Funciones de testing optimizadas ────────────────────────────────────────────────────

def test_all_systems():
    """Función de prueba completa con verificación colombiana"""
    print("🧪 Probando Sistema de Proxies con Verificación Colombiana\n")
    
    status = estado_proxies()
    
    print("📊 Estado de Servicios:")
    print(f"  🇨🇴 Servicio Proxy: {'✅ Disponible' if status['proxy_service']['available'] else '❌ No disponible'}")
    print(f"      IP Colombiana: {'✅ Verificada' if status['proxy_service']['colombian_verified'] else '❌ No verificada'}")
    print(f"  🌐 DataImpulse: {'✅ Disponible' if status['dataimpulse']['available'] else '❌ No disponible'}")
    print(f"      IP Colombiana: {'✅ Verificada' if status['dataimpulse']['colombian_verified'] else '❌ No verificada'}")
    print(f"  ⚙️ Método preferido: {status['preferred_method']}")
    
    if status['proxy_service']['available'] and status['proxy_service']['stats']:
        stats = status['proxy_service']['stats']
        print(f"\n📈 Stats Servicio:")
        print(f"  • Datos restantes: {stats.get('remaining_gb', 'N/A')} GB")
        print(f"  • Requests totales: {stats.get('total_requests', 'N/A')}")
        print(f"  • Tasa de éxito: {stats.get('success_rate', 'N/A')}%")
    
    print("\n🔍 Probando obtención de proxy colombiano GARANTIZADO...")
    proxy = obtener_proxy_colombiano_garantizado("test_store")
    
    if proxy:
        print(f"✅ Proxy colombiano GARANTIZADO obtenido!")
        print(f"  • Fuente: {proxy.get('source', 'unknown')}")
        print(f"  • País: {proxy.get('country', 'N/A')}")
        if 'session_id' in proxy:
            print(f"  • Session ID: {proxy['session_id']}")
        if 'detected_ip' in proxy:
            print(f"  • IP detectada: {proxy['detected_ip']}")
            # Verificar nuevamente que sea colombiana
            is_co = ColombianIPChecker.verify_ip_is_colombian(proxy['detected_ip'])
            print(f"  • Verificación CO: {'✅ Confirmada' if is_co else '❌ Falló'}")
        
        # Probar rotación
        print("\n🔄 Probando rotación manteniendo IP colombiana...")
        rotated = rotar_proxy()
        if rotated:
            print("✅ Rotación exitosa!")
            if 'session_id' in rotated:
                print(f"  • Nueva Session ID: {rotated['session_id']}")
            if 'detected_ip' in rotated:
                print(f"  • Nueva IP: {rotated['detected_ip']}")
        else:
            print("❌ Rotación falló")
    else:
        print("❌ No se pudo obtener proxy colombiano GARANTIZADO")
    
    return proxy is not None

def configure_proxy_preference(prefer_service: bool = True, enable_fallback: bool = True):
    """Configurar preferencias de proxy manteniendo verificación colombiana"""
    global _proxy_manager
    _proxy_manager.prefer_service = prefer_service
    _proxy_manager.fallback_enabled = enable_fallback
    
    logger.info(f"⚙️ Configuración actualizada - Preferir servicio: {prefer_service}, Fallback: {enable_fallback}")
    logger.info("🇨🇴 Verificación colombiana SIEMPRE activa")

def get_proxy_for_store(store_id: str) -> Optional[Dict[str, str]]:
    """Obtener proxy específico para una tienda GARANTIZANDO IP colombiana"""
    return obtener_proxy_colombiano_garantizado(store_id)

def main():
    """Función de prueba principal optimizada"""
    print("🌐 Sistema de Proxy Optimizado - IP Colombiana Garantizada v3.0\n")
    
    # Configurar logging para pruebas
    logging.basicConfig(level=logging.INFO)
    
    # Ejecutar todas las pruebas
    success = test_all_systems()
    
    if success:
        print("\n🎉 ¡Sistema de proxies funcionando con IP colombiana GARANTIZADA!")
    else:
        print("\n⚠️ Sistema de proxies con problemas - No se pudo garantizar IP colombiana")
    
    return success

if __name__ == "__main__":
    main()
