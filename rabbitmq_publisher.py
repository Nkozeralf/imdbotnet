# rabbitmq_publisher.py
import pika
import json
import logging
from datetime import datetime
from typing import Dict, Any

class RabbitMQPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.rabbitmq_url = "amqp://admin:admin123@192.168.80.23:5672/shopifybot"
        
    def connect(self):
        """Conectar a RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            
            # Declarar colas
            self.setup_queues()
            logging.info("✅ Conectado a RabbitMQ")
            return True
        except Exception as e:
            logging.error(f"❌ Error conectando a RabbitMQ: {e}")
            return False
    
    def setup_queues(self):
        """Crear colas necesarias"""
        queues = [
            'pedidos.iniciados',
            'pedidos.completados', 
            'pedidos.fallidos',
            'system.stats',
            'system.alerts'
        ]
        
        for queue in queues:
            self.channel.queue_declare(queue=queue, durable=True)
    
    def publish_pedido_iniciado(self, tienda: str, datos: Dict[str, Any]):
        """Publicar cuando se inicia un pedido"""
        message = {
            'tipo': 'pedido_iniciado',
            'timestamp': datetime.now().isoformat(),
            'tienda': tienda,
            'datos': datos
        }
        self._publish('pedidos.iniciados', message)
    
    def publish_pedido_completado(self, result: Dict[str, Any]):
        """Publicar cuando se completa un pedido"""
        message = {
            'tipo': 'pedido_completado',
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
        self._publish('pedidos.completados', message)
    
    def publish_pedido_fallido(self, result: Dict[str, Any]):
        """Publicar cuando falla un pedido"""
        message = {
            'tipo': 'pedido_fallido', 
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
        self._publish('pedidos.fallidos', message)
    
    def _publish(self, queue: str, message: Dict[str, Any]):
        """Publicar mensaje a cola específica"""
        try:
            if not self.channel:
                self.connect()
                
            self.channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # Mensaje persistente
            )
            logging.debug(f"📤 Mensaje enviado a {queue}")
        except Exception as e:
            logging.error(f"❌ Error publicando a {queue}: {e}")
