import pika
from typing import List
from app.models.movie import Movie

# Параметры подключения
connection_params = pika.ConnectionParameters(
    host='rabbitmq',  # Замените на адрес вашего RabbitMQ сервера
    port=5672,          # Порт по умолчанию для RabbitMQ
    virtual_host='/',   # Виртуальный хост (обычно '/')
    credentials=pika.PlainCredentials(
        username='rmuser',  # Имя пользователя по умолчанию
        password='rmpassword'   # Пароль по умолчанию
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)

def send_task(message:str):
    """Отправка ML задачи"""
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Имя очереди
        queue_name = 'ml_task_queue'

        # Отправка сообщения
        channel.queue_declare(queue=queue_name)  # Создание очереди (если не существует)

        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message
        )

        # Закрытие соединения
        connection.close()
    except Exception as e:
            raise

def send_result(result_data: List[Movie]):
    """Отправка результата ML задачи"""
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        queue_name = 'ml_result_queue'
        channel.queue_declare(queue=queue_name)
        
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=result_data
        )

        # Закрытие соединения
        connection.close()
        
    except Exception as e:
        raise
