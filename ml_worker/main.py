import pika
import time
import json
import sys
from loguru import logger
from constants import ModelTypes
from config import get_settings
from embedding import EmbeddingGenerator


# Настройка логирования
logger.remove()
logger.add(sys.stderr, level="INFO")

# Инициализация модели
embedding_generator = EmbeddingGenerator(ModelTypes.MULTILINGUAL.value)

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

# Названия очередей (RPC style: requests sent to task_queue, replies go to reply_to)
task_queue = 'ml_task_queue'

channel = connection.channel()
channel.queue_declare(queue=task_queue, durable=False)

# Функция генерации ембендингов
def get_embedding(input_text: str):
    return embedding_generator.get_embedding(input_text)

def send_result_to_queue(result_data, properties):
    """Отправка результата в очередь результатов"""
    try:        
        channel.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            body=json.dumps(result_data),
            properties=pika.BasicProperties(
                correlation_id=properties.correlation_id
            )
        )
        logger.info(f"Result sent to queue: {result_data}")
    except Exception as e:
        logger.error(f"Error sending result to queue: {e}")

def on_request(ch, method, properties, body):
    try:
        logger.info(f"Received message: {body}")
        
        # Парсинг входящего сообщения
        data = json.loads(body)
        input_text = data.get('text')
        
        if not input_text:
            raise ValueError("No 'text' in message")
        
        if len(input_text) == 0:
            raise ValueError("Request is empty")
        
        # Обработка рекомендации
        start_time = time.time()
        try:
            request_embedding = get_embedding(input_text)
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise
        processing_time = time.time() - start_time
                
        # Отправка результата
        result_data = {
            "request_embedding": request_embedding,
            "processing_time": processing_time,
            "status": "success"
        }
        
        send_result_to_queue(result_data, properties)
        
        # Подтверждение обработки
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(
    queue=task_queue,
    on_message_callback=on_request,
    auto_ack=False
)

logger.info('Waiting for recommendation requests. To exit press Ctrl+C')
channel.start_consuming()