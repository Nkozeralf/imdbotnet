# launcher_optimized.py - Launcher actualizado
import os
import time
import logging
from rich.console import Console

from bot_executor import ejecutar_lote_pedidos, get_system_status
from limpiador_logs import limpiar_logs

logger = logging.getLogger("launcher_optimized")
console = Console()

def listar_tiendas() -> list:
    """Lista tiendas disponibles"""
    tiendas_dir = "tiendas"
    if not os.path.isdir(tiendas_dir):
        return []
    
    return sorted([f[:-5] for f in os.listdir(tiendas_dir) if f.endswith('.json')])

def mostrar_estado_sistema():
    """Muestra estado del sistema"""
    console.print("\n[bold blue]📊 Estado del Sistema[/]")
    console.print("=" * 50)
    
    try:
        status = get_system_status()
        
        ready = status.get("system_ready", False)
        status_text = "[green]✅ Listo[/]" if ready else "[red]❌ Problemas[/]"
        console.print(f"Estado general: {status_text}")
        
        network = status.get("network_quality", {})
        latency = network.get("latency_ms", 0)
        quality = network.get("quality", "unknown")
        
        console.print(f"Red: {quality} ({latency:.0f}ms)")
        
        store_count = status.get("store_count", 0)
        console.print(f"Tiendas: {store_count}")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/]")

def ejecutar_rotacion_vpn():
    """Ejecuta rotación de VPN"""
    vpn_script = "surfshark/surfshark_rotate.sh"
    
    if os.path.exists(vpn_script):
        logger.info("🔁 Ejecutando rotación de VPN...")
        os.system(f"sudo bash {vpn_script}")
        time.sleep(8)
        
        try:
            import requests
            nueva_ip = requests.get("https://api.ipify.org", timeout=5).text
            logger.info(f"🌐 Nueva IP: {nueva_ip}")
        except:
            logger.info("🌐 IP no verificable")
    else:
        logger.warning("⚠️ Script VPN no encontrado")

def seleccionar_tiendas(tiendas_disponibles: list) -> list:
    """Seleccionar tiendas"""
    if not tiendas_disponibles:
        console.print("[red]❌ No hay tiendas[/]")
        return []
    
    console.print(f"\n[bold]📋 Tiendas ({len(tiendas_disponibles)}):[/]")
    for idx, tienda in enumerate(tiendas_disponibles, 1):
        console.print(f"  {idx}. {tienda}")
    
    while True:
        try:
            seleccion = input("\n💡 Selecciona (ej: 1,2 o 'all'): ").strip()
            
            if seleccion.lower() == 'all':
                return tiendas_disponibles.copy()
            
            indices = []
            for parte in seleccion.split(','):
                if parte.strip().isdigit():
                    idx = int(parte.strip()) - 1
                    if 0 <= idx < len(tiendas_disponibles):
                        indices.append(idx)
            
            if indices:
                return [tiendas_disponibles[i] for i in indices]
            else:
                raise ValueError("Selección inválida")
                
        except ValueError as e:
            console.print(f"[red]❌ {e}[/]")

def configurar_ejecucion() -> dict:
    """Configurar parámetros"""
    config = {}
    
    while True:
        try:
            n = int(input("🔢 ¿Pedidos por tienda?: "))
            if n > 0:
                config["pedidos_por_tienda"] = n
                break
        except ValueError:
            console.print("[red]❌ Número inválido[/]")
    
    console.print("\n[bold]⚙️ Modo:[/]")
    console.print("1. 🐢 Estándar")
    console.print("2. ⚡ Rápido") 
    console.print("3. 🛡️ Robusto")
    
    modo = input("Modo (1-3): ").strip()
    modos = {"1": "standard", "2": "fast", "3": "robust"}
    config["execution_mode"] = modos.get(modo, "standard")
    
    try:
        concurrent = input("🔄 Concurrencia [3]: ").strip()
        config["max_concurrent"] = int(concurrent) if concurrent else 3
    except:
        config["max_concurrent"] = 3
    
    config["usar_intervalos"] = input("⏱️ ¿Intervalos aleatorios? (s/N): ").lower() == 's'
    config["enable_telegram"] = input("📱 ¿Notificaciones Telegram? (S/n): ").lower() != 'n'
    
    return config

def main():
    """Función principal"""
    console.print("\n[bold green]🛒 Shopify Bot - Sistema Optimizado[/]")
    console.print("[dim]Arquitectura Modular v2.0[/]\n")
    
    while True:
        mostrar_estado_sistema()
        
        console.print("\n[bold]Opciones:[/]")
        console.print("1. 🚀 Ejecutar pedidos")
        console.print("2. 🔁 Rotar VPN")
        console.print("3. 🧹 Limpiar logs")
        console.print("4. 📊 Estado detallado")
        console.print("0. ❌ Salir")
        
        opcion = input("\n🎯 Opción: ").strip()
        
        if opcion == "0":
            console.print("\n[yellow]👋 Hasta luego![/]")
            break
            
        elif opcion == "1":
            tiendas_disponibles = listar_tiendas()
            if not tiendas_disponibles:
                console.print("[red]❌ No hay tiendas[/]")
                continue
            
            tiendas_seleccionadas = seleccionar_tiendas(tiendas_disponibles)
            if not tiendas_seleccionadas:
                continue
            
            config = configurar_ejecucion()
            
            total = len(tiendas_seleccionadas) * config["pedidos_por_tienda"]
            console.print(f"\n[bold green]📋 Resumen:[/]")
            console.print(f"  🏪 Tiendas: {len(tiendas_seleccionadas)}")
            console.print(f"  🔢 Total pedidos: {total}")
            console.print(f"  ⚙️ Modo: {config['execution_mode']}")
            
            if input("\n✅ ¿Continuar? (s/N): ").lower() != 's':
                continue
            
            ejecutar_rotacion_vpn()
            
            console.print(f"\n[bold blue]🚀 Ejecutando {total} pedidos...[/]")
            
            resultado = ejecutar_lote_pedidos(
                tiendas=tiendas_seleccionadas,
                pedidos_por_tienda=config["pedidos_por_tienda"],
                execution_mode=config["execution_mode"],
                max_concurrent=config["max_concurrent"],
                usar_intervalos=config["usar_intervalos"],
                enable_telegram=config["enable_telegram"]
            )
            
            if resultado["exito"]:
                console.print(f"\n[green]🎉 Completado![/]")
                console.print(f"  ✅ Exitosos: {resultado['completados']}")
                console.print(f"  ❌ Fallidos: {resultado['fallidos']}")
                console.print(f"  📈 Éxito: {resultado['tasa_exito']:.1f}%")
            else:
                console.print(f"\n[red]❌ Error: {resultado.get('mensaje')}[/]")
            
            input("\nPresiona Enter...")
            
        elif opcion == "2":
            console.print("\n[bold blue]🔁 Rotando VPN...[/]")
            ejecutar_rotacion_vpn()
            input("Presiona Enter...")
            
        elif opcion == "3":
            console.print("\n[bold yellow]🧹 Limpiando logs...[/]")
            limpiar_logs(confirmado=True)
            console.print("[green]✅ Limpieza completada[/]")
            input("Presiona Enter...")
            
        elif opcion == "4":
            console.print("\n[bold blue]📊 Estado detallado:[/]")
            try:
                status = get_system_status()
                import json
                console.print(json.dumps(status, indent=2, ensure_ascii=False))
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/]")
            input("\nPresiona Enter...")
            
        else:
            console.print(f"[red]❌ Opción inválida[/]")

if __name__ == '__main__':
    if not os.path.exists("bot_core.py") or not os.path.exists("bot_executor.py"):
        print("❌ Sistema no migrado. Ejecutar deploy_manual.sh primero.")
        exit(1)
    
    main()
