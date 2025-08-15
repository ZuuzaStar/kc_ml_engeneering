import pika
import time
import json
import sys
from loguru import logger

from ml_worker.constants import ModelTypes
from .config import get_settings
from sentence_transformers import SentenceTransformer

# Добавляем путь к модулям app
sys.path.append('/app')

# Настройка логирования
logger.remove()
logger.add(sys.stderr, level="INFO")

# Инициализация рекомендательной системы (модель загружается внутри MovieRecommender)
model = SentenceTransformer('sentence-transformers/' + ModelTypes.BASIC.value)

# Подключение к RabbitMQ (как в учебном примере)
settings = get_settings()
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=settings.RABBITMQ_HOST,
    port=settings.RABBITMQ_PORT,
    virtual_host='/',
    credentials=pika.PlainCredentials(
        username=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    ),
    heartbeat=30,
    blocked_connection_timeout=2
))
channel = connection.channel()
queue_name = 'ml_task_queue'
channel.queue_declare(queue=queue_name)

def send_result_to_queue(result_data):
    """Отправка результата в очередь результатов"""
    try:
        result_queue = 'ml_result_queue'
        channel.queue_declare(queue=result_queue, durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key=result_queue,
            body=json.dumps(result_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Сделать сообщение постоянным
            )
        )
        logger.info(f"Result sent to queue: {result_data}")
    except Exception as e:
        logger.error(f"Error sending result to queue: {e}")

def callback(ch, method, properties, body):
    try:
        logger.info(f"Received message: {body}")
        
        # Парсинг входящего сообщения
        data = json.loads(body)
        input_text = data.get('text')
        
        if not input_text:
            raise ValueError("No 'text' in message")
        
        # Обработка рекомендации
        start_time = time.time()
        recommendations =  d
        processing_time = time.time() - start_time
        
        # Преобразование результатов в словари
        recommendations_data = []
        for movie in recommendations:
            recommendations_data.append({
                "id": movie.id,
                "title": movie.title,
                "description": movie.description,
                "year": movie.year,
                "genres": movie.genres
            })
        
        logger.info(f"Generated {len(recommendations_data)} recommendations in {processing_time:.2f}s")
        
        # Отправка результата в очередь результатов
        result_data = {
            "recommendations": recommendations_data,
            "processing_time": processing_time,
            "status": "success"
        }
        
        # Отправка в очередь результатов
        send_result_to_queue(result_data)
        
        # Подтверждение обработки
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# Настройка потребителя (как в учебном примере)
channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=False
)

logger.info('Waiting for recommendation requests. To exit press Ctrl+C')
channel.start_consuming()