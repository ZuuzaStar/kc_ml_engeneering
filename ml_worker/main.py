import pika
import time
import logging
import json
from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select
from app.services.crud import movie_service as MovieService
from app.database.database import engine
from app.models.movie import Movie
from app.models.constants import ModelTypes

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация модели (вынесена в глобальную область для однократной загрузки)
model = SentenceTransformer('sentence-transformers/' + ModelTypes.BASIC.value)

# Подключение к RabbitMQ (как в учебном примере)
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host='rabbitmq',
    port=5672,
    virtual_host='/',
    credentials=pika.PlainCredentials(
        username='rmuser',
        password='rmpassword'
    ),
    heartbeat=30,
    blocked_connection_timeout=2
))
channel = connection.channel()
queue_name = 'ml_task_queue'
channel.queue_declare(queue=queue_name)

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
        recommendations = MovieService.process_recommendation(model, input_text)
        processing_time = time.time() - start_time
        
        logger.info(f"Generated {len(recommendations)} recommendations in {processing_time:.2f}s")
        
        # Отправка результата в очередь результатов
        result_data = {
            "recommendations": recommendations,
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