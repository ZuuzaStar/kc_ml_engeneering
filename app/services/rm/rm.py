import pika
from typing import List, Dict, Any, Optional
from models.movie import Movie
from database.config import get_settings
import json
from loguru import logger


settings = get_settings()

# Параметры подключения
connection_params = pika.ConnectionParameters(
    host=settings.RABBITMQ_HOST,
    port=settings.RABBITMQ_PORT,
    virtual_host='/',
    credentials=pika.PlainCredentials(
        username=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASSWORD
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)


def send_task(message: str) -> bool:
    """
    Отправка ML задачи в очередь.
    
    Args:
        message (str): Текстовое сообщение для обработки
        
    Returns:
        bool: True если задача отправлена успешно
        
    Raises:
        Exception: При ошибке отправки
    """
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Имя очереди
        queue_name = 'ml_task_queue'

        # Создание очереди (если не существует)
        channel.queue_declare(queue=queue_name, durable=True)

        # Подготовка данных
        data = {"text": message}
        
        # Отправка сообщения
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Сделать сообщение постоянным
            )
        )

        logger.info(f"Задача отправлена в очередь: {message}")
        
        # Закрытие соединения
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке задачи: {e}")
        raise


def send_result(result_data: Dict[str, Any]) -> bool:
    """
    Отправка результата ML задачи в очередь результатов.
    
    Args:
        result_data (Dict[str, Any]): Результат обработки в виде словаря
        
    Returns:
        bool: True если результат отправлен успешно
        
    Raises:
        Exception: При ошибке отправки
    """
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        queue_name = 'ml_result_queue'
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Сериализация данных в JSON
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(result_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Сделать сообщение постоянным
            )
        )

        logger.info(f"Результат отправлен в очередь: {result_data.get('status', 'unknown')}")
        
        # Закрытие соединения
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке результата: {e}")
        raise


def get_result(timeout: int = 30) -> Optional[Dict[str, Any]]:
    """
    Получение результата из очереди результатов.
    
    Args:
        timeout (int): Таймаут ожидания в секундах
        
    Returns:
        Optional[Dict[str, Any]]: Результат или None если таймаут
    """
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        queue_name = 'ml_result_queue'
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Получение сообщения с таймаутом
        method_frame, header_frame, body = channel.basic_get(queue=queue_name)
        
        if method_frame:
            result = json.loads(body)
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            logger.info("Результат получен из очереди")
            connection.close()
            return result
        else:
            logger.warning(f"Таймаут ожидания результата ({timeout}с)")
            connection.close()
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при получении результата: {e}")
        raise


def send_movie_list_result(movies: List[Movie]) -> bool:
    """
    Отправка списка фильмов как результат.
    
    Args:
        movies (List[Movie]): Список фильмов
        
    Returns:
        bool: True если результат отправлен успешно
    """
    try:
        # Преобразование объектов Movie в словари
        movie_data = []
        for movie in movies:
            movie_data.append({
                'id': movie.id,
                'title': movie.title,
                'year': movie.year,
                'description': movie.description,
                'genres': movie.genres
            })
        
        result_data = {
            'status': 'success',
            'recommendations': movie_data,
            'count': len(movie_data)
        }
        
        return send_result(result_data)
        
    except Exception as e:
        logger.error(f"Ошибка при отправке списка фильмов: {e}")
        raise


def check_queue_status() -> Dict[str, Any]:
    """
    Проверка статуса очередей.
    
    Returns:
        Dict[str, Any]: Информация о состоянии очередей
    """
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        task_queue = 'ml_task_queue'
        result_queue = 'ml_result_queue'
        
        # Объявляем очереди
        channel.queue_declare(queue=task_queue, durable=True)
        channel.queue_declare(queue=result_queue, durable=True)
        
        # Получаем информацию о очередях
        task_info = channel.queue_declare(queue=task_queue, durable=True, passive=True)
        result_info = channel.queue_declare(queue=result_queue, durable=True, passive=True)
        
        status = {
            'task_queue': {
                'name': task_queue,
                'message_count': task_info.method.message_count,
                'consumer_count': task_info.method.consumer_count
            },
            'result_queue': {
                'name': result_queue,
                'message_count': result_info.method.message_count,
                'consumer_count': result_info.method.consumer_count
            }
        }
        
        connection.close()
        logger.info(f"Статус очередей: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса очередей: {e}")
        raise


def purge_queues() -> bool:
    """
    Очистка всех очередей.
    
    Returns:
        bool: True если очереди очищены успешно
    """
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()

        task_queue = 'ml_task_queue'
        result_queue = 'ml_result_queue'
        
        # Очищаем очереди
        channel.queue_purge(queue=task_queue)
        channel.queue_purge(queue=result_queue)
        
        connection.close()
        logger.info("Очереди очищены")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при очистке очередей: {e}")
        raise
