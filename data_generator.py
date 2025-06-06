# data_generator_mejorado.py
import random
import secrets
from typing import Dict, List

class ColombianDataGenerator:
    """Generador de datos realistas para Colombia"""
    
    # Nombres colombianos comunes
    NOMBRES_MASCULINOS = [
        "Carlos", "Luis", "José", "Juan", "Miguel", "Andrés", "David", "Daniel", 
        "Alejandro", "Felipe", "Santiago", "Sebastián", "Nicolás", "Mateo", "Diego",
        "Gabriel", "Óscar", "Javier", "Fernando", "Ricardo", "Fabián", "Mauricio",
        "Édgar", "Iván", "Raúl", "Héctor", "Arturo", "Rubén", "Guillermo", "Sergio"
    ]
    
    NOMBRES_FEMENINOS = [
        "María", "Ana", "Carmen", "Luz", "Rosa", "Diana", "Sandra", "Patricia", 
        "Claudia", "Mónica", "Andrea", "Paola", "Natalia", "Carolina", "Adriana",
        "Marcela", "Alejandra", "Catalina", "Viviana", "Esperanza", "Gloria", "Pilar",
        "Beatriz", "Isabel", "Teresa", "Rocío", "Amparo", "Mercedes", "Consuelo", "Blanca"
    ]
    
    # Apellidos colombianos comunes
    APELLIDOS = [
        "García", "Rodríguez", "González", "Hernández", "López", "Martínez", "Pérez", 
        "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Reyes",
        "Morales", "Jiménez", "Álvarez", "Ruiz", "Gutiérrez", "Ortiz", "Serrano", 
        "Castro", "Vargas", "Ramos", "Guerrero", "Medina", "Cruz", "Aguilar", "Delgado",
        "Herrera", "Mendoza", "Silva", "Rojas", "Vega", "Castillo", "Moreno", "Romero",
        "Suárez", "Peña", "Valencia", "Ospina", "Quintero", "Arbeláez", "Betancur"
    ]
    
    # Direcciones típicas colombianas
    TIPOS_VIA = ["Calle", "Carrera", "Avenida", "Diagonal", "Transversal", "Circular"]
    COMPLEMENTOS_DIRECCION = [
        "Sur", "Norte", "Este", "Oeste", "A", "B", "C", "Bis", "Bis A", "Bis B"
    ]
    
    # Barrios por ciudad principal
    BARRIOS_BOGOTA = [
        "Chapinero", "Zona Rosa", "La Candelaria", "Teusaquillo", "Suba", "Engativá",
        "Kennedy", "Bosa", "Ciudad Bolívar", "Usaquén", "Fontibón", "Puente Aranda",
        "Los Mártires", "Antonio Nariño", "Barrios Unidos", "La Macarena", "Chicó",
        "El Poblado", "Laureles", "Belén", "Robledo", "Aranjuez", "Manrique", "Villa Hermosa"
    ]
    
    BARRIOS_MEDELLIN = [
        "El Poblado", "Laureles", "Belén", "Robledo", "Aranjuez", "Manrique", 
        "Villa Hermosa", "Buenos Aires", "La Candelaria", "La América", "San Javier",
        "El Dorado", "Guayabal", "Castilla", "Doce de Octubre", "Santa Cruz"
    ]
    
    BARRIOS_CALI = [
        "San Fernando", "Ciudad Jardín", "El Ingenio", "Chipichape", "Versalles",
        "Tequendama", "San Antonio", "La Flora", "Normandía", "El Peñón", "Meléndez",
        "Ciudad Córdoba", "El Caney", "Pance", "Aguablanca", "Siloé"
    ]
    
    BARRIOS_CARTAGENA = [
        "Bocagrande", "El Laguito", "Castillogrande", "Manga", "Pie de la Popa",
        "Getsemaní", "Centro Histórico", "La Matuna", "El Cabrero", "Crespo",
        "Torices", "Espinal", "Olaya Herrera", "El Pozón", "Nelson Mandela"
    ]
    
    # Operadores móviles colombianos
    OPERADORES = {
    # Operadores principales con mayor cobertura y fiabilidad
        "Claro": ["300", "301", "302", "303", "304", "305", "320", "321"],
        "Movistar": ["310", "311", "312", "313", "314", "315"],
        #"Tigo": ["323", "324", "325", "326", "327"],
        
        # Operadores secundarios (opcional, si realmente los necesitas)
        # "WOM": ["380", "381"]
    }
    
    # Dominios de email populares en Colombia
    DOMINIOS_EMAIL = [
        "gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "live.com",
        "yahoo.es", "hotmail.es", "correounivalle.edu.co", "unal.edu.co",
        "javeriana.edu.co", "uniandes.edu.co", "usergioarboleda.edu.co"
    ]
    
    @classmethod
    def generar_nombre_completo(cls) -> Dict[str, str]:
        """Genera nombre y apellido colombiano realista"""
        es_masculino = random.choice([True, False])
        
        if es_masculino:
            nombre = random.choice(cls.NOMBRES_MASCULINOS)
        else:
            nombre = random.choice(cls.NOMBRES_FEMENINOS)
        
        # En Colombia es común tener dos apellidos
        apellido1 = random.choice(cls.APELLIDOS)
        apellido2 = random.choice(cls.APELLIDOS)
        
        return {
            "nombre": nombre,
            "apellido": f"{apellido1} {apellido2}",
            "genero": "M" if es_masculino else "F"
        }
    
    @classmethod
    def generar_telefono(cls) -> str:
        """Genera número de teléfono móvil colombiano válido"""
        operador = random.choice(list(cls.OPERADORES.keys()))
        prefijos = cls.OPERADORES[operador]
        prefijo = random.choice(prefijos)
        
        # Generar 7 dígitos restantes (evitar patrones como 0000000)
        while True:
            resto = ''.join([str(random.randint(0, 9)) for _ in range(7)])
            # Evitar números que terminen en muchos ceros seguidos
            if not (resto.endswith('0000') or resto == '0000000'):
                break
        
        telefono = f"{prefijo}{resto}"
        
        # Verificar que sea exactamente 10 dígitos
        if len(telefono) != 10:
            return cls.generar_telefono()  # Recursión si hay error
            
        return telefono
    
    @classmethod
    def generar_cedula(cls) -> str:
        """Genera un número de cédula de 8-10 dígitos (sin DV)"""
        longitud = random.choice([8, 9, 10])
        primer_dig = random.randint(1, 9)              # que no empiece en 0
        resto = ''.join(str(random.randint(0, 9)) for _ in range(longitud - 1))
        return f"{primer_dig}{resto}"
    
    @classmethod
    def generar_email(cls, nombre: str, apellido: str) -> str:
        """Genera email basado en nombre y apellido"""
        dominio = random.choice(cls.DOMINIOS_EMAIL)
        
        # Limpiar nombre y apellido
        nombre_clean = nombre.lower().replace(" ", "")
        apellido_clean = apellido.split()[0].lower()  # Solo primer apellido
        
        # Diferentes formatos de email
        formatos = [
            f"{nombre_clean}.{apellido_clean}",
            f"{nombre_clean}{apellido_clean}",
            f"{nombre_clean[0]}{apellido_clean}",
            f"{nombre_clean}.{apellido_clean}{random.randint(1, 99)}",
            f"{nombre_clean}{random.randint(1, 999)}"
        ]
        
        formato = random.choice(formatos)
        return f"{formato}@{dominio}"
    
    @classmethod
    def generar_direccion(cls) -> Dict[str, str]:
        """Genera dirección colombiana realista"""
        tipo_via = random.choice(cls.TIPOS_VIA)
        numero_principal = random.randint(1, 200)
        numero_secundario = random.randint(1, 99)
        numero_terciario = random.randint(1, 99)
        
        # Posible complemento
        complemento = ""
        if random.random() < 0.3:  # 30% de probabilidad
            complemento = f" {random.choice(cls.COMPLEMENTOS_DIRECCION)}"
        
        direccion = f"{tipo_via} {numero_principal}{complemento} # {numero_secundario} - {numero_terciario}"
        
        # Información adicional del apartamento/casa
        apartamento_tipos = ["Apto", "Apt", "Casa", "Local", "Of"]
        apartamento_numero = f"{random.choice(apartamento_tipos)} {random.randint(1, 500)}"
        
        # Torres/bloques (para apartamentos)
        complemento_apto = ""
        if "Apt" in apartamento_numero and random.random() < 0.4:
            complemento_apto = f", Torre {random.choice(['A', 'B', 'C', '1', '2', '3'])}"
            if random.random() < 0.3:
                complemento_apto += f", Bloque {random.randint(1, 10)}"
        
        return {
            "direccion": direccion,
            "apartamento": apartamento_numero + complemento_apto,
            "direccion_completa": f"{direccion}, {apartamento_numero}{complemento_apto}"
        }
    
    @classmethod
    def generar_barrio(cls, departamento: str = None) -> str:
        """Genera barrio según el departamento"""
        barrios_por_dept = {
            "CUN": cls.BARRIOS_BOGOTA,  # Cundinamarca (Bogotá)
            "ANT": cls.BARRIOS_MEDELLIN,  # Antioquia (Medellín)
            "VAC": cls.BARRIOS_CALI,     # Valle del Cauca (Cali)
            "BOL": cls.BARRIOS_CARTAGENA  # Bolívar (Cartagena)
        }
        
        if departamento and departamento in barrios_por_dept:
            return random.choice(barrios_por_dept[departamento])
        
        # Barrio genérico si no coincide
        todos_barrios = (cls.BARRIOS_BOGOTA + cls.BARRIOS_MEDELLIN + 
                        cls.BARRIOS_CALI + cls.BARRIOS_CARTAGENA)
        return random.choice(todos_barrios)
    
    @classmethod
    def generar_datos_completos(cls, departamento: str = None) -> Dict[str, str]:
        """Genera todos los datos necesarios para un pedido"""
        # Información personal
        persona = cls.generar_nombre_completo()
        telefono = cls.generar_telefono()
        cedula = cls.generar_cedula() 
        email = cls.generar_email(persona["nombre"], persona["apellido"])
        
        # Información de dirección
        direccion_info = cls.generar_direccion()
        barrio = cls.generar_barrio(departamento)
        
        return {
            "nombre": persona["nombre"],
            "apellido": persona["apellido"],
            "telefono": telefono,
            "email": email,
            "cedula": cedula,
            "direccion": direccion_info["direccion"],
            "apartamento": direccion_info["apartamento"],
            "barrio": barrio,
            "genero": persona["genero"],
            
            # Aliases para compatibilidad con diferentes formularios
            "civic_number": direccion_info["apartamento"],
            "address": direccion_info["direccion"],
            "phone": telefono,
            "first_name": persona["nombre"],
            "last_name": persona["apellido"],
            "note": cedula,                   # ← NUEVA (algunos pop-ups usan “note”)
            "numero_cedula": cedula,          # ← opcional
            
            # Campos adicionales que pueden aparecer en formularios
            "correo": email,
            "correo_electronico": email,
            "mail": email,
            "e_mail": email,
            "celular": telefono,
            "movil": telefono,
            "telefono_movil": telefono,
            "numero_telefono": telefono
        }

# Funciones de compatibilidad con el sistema existente
def generar_datos(departamento: str = None) -> Dict[str, str]:
    """Función principal de compatibilidad"""
    return ColombianDataGenerator.generar_datos_completos(departamento)

def generar_telefono_colombiano() -> str:
    """Genera solo teléfono"""
    return ColombianDataGenerator.generar_telefono()

def generar_email_colombiano(nombre: str, apellido: str) -> str:
    """Genera solo email"""
    return ColombianDataGenerator.generar_email(nombre, apellido)

def generar_direccion_colombiana() -> str:
    """Genera solo dirección"""
    direccion_info = ColombianDataGenerator.generar_direccion()
    return direccion_info["direccion"]

def validar_telefono_colombiano(telefono: str) -> bool:
    """Valida si un teléfono es formato colombiano válido"""
    # Limpiar el teléfono de espacios y caracteres especiales
    telefono_clean = ''.join(filter(str.isdigit, telefono))
    
    if len(telefono_clean) != 10:
        return False
    
    prefijo = telefono_clean[:3]
    todos_prefijos = []
    for prefijos in ColombianDataGenerator.OPERADORES.values():
        todos_prefijos.extend(prefijos)
    
    is_valid = prefijo in todos_prefijos
    
    # Log para debug
    if not is_valid:
        print(f"❌ Teléfono inválido: {telefono} (prefijo {prefijo} no reconocido)")
    
    return is_valid

def test_generator():
    """Función de prueba del generador"""
    print("🧪 Probando Generador de Datos Colombianos\n")
    
    # Generar 5 ejemplos
    for i in range(5):
        datos = generar_datos()
        print(f"📋 Ejemplo {i+1}:")
        print(f"  👤 Nombre: {datos['nombre']} {datos['apellido']}")
        print(f"  📱 Teléfono: {datos['telefono']} ({'✅ Válido' if validar_telefono_colombiano(datos['telefono']) else '❌ Inválido'})")
        print(f"  📧 Email: {datos['email']}")
        print(f"  🏠 Dirección: {datos['direccion']}")
        print(f"  🏢 Apartamento: {datos['apartamento']}")
        print(f"  🏘️ Barrio: {datos['barrio']}")
        print(f"  ⚧️ Género: {datos['genero']}")
        print()
    
    # Estadísticas de operadores
    operadores_count = {}
    for _ in range(100):
        tel = generar_telefono_colombiano()
        prefijo = tel[:3]
        for op, prefijos in ColombianDataGenerator.OPERADORES.items():
            if prefijo in prefijos:
                operadores_count[op] = operadores_count.get(op, 0) + 1
                break
    
    print("📊 Distribución de Operadores (100 muestras):")
    for op, count in operadores_count.items():
        print(f"  📶 {op}: {count}%")

if __name__ == "__main__":
    test_generator()
