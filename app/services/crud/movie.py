from models.movie import Movie
from sqlmodel import Session, select
import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from loguru import logger
from sentence_transformers import SentenceTransformer


def change_title(movie: Movie, new_title: str, session: Session) -> Movie:
    """Возможность исправлять ошибки в названии"""
    if not new_title or len(new_title.strip()) < 1:
        raise ValueError("Название фильма должно быть не короче одного символа")
    
    try:
        movie.title = new_title.strip()
        session.add(movie)
        session.commit()
        session.refresh(movie)
        logger.info(f"Название фильма {movie.id} изменено на: {new_title}")
        return movie
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при изменении названия фильма: {e}")
        raise


def change_description(movie: Movie, new_description: str, session: Session) -> Movie:
    """Возможность исправлять ошибки в описании"""
    if not new_description or len(new_description.strip()) < 10:
        raise ValueError("Описание фильма не должно быть короче 10 символов")
    
    try:
        movie.description = new_description.strip()
        session.add(movie)
        session.commit()
        session.refresh(movie)
        logger.info(f"Описание фильма {movie.id} изменено")
        return movie
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при изменении описания фильма: {e}")
        raise


def get_movie_by_id(id: int, session: Session) -> Optional[Movie]:
    """
    Получить фильм по ID.
    
    Args:
        id: ID фильма
        session: сессия базы данных
    
    Returns:
        Optional[Movie]: Найденный фильм или None
    """
    try:
        statement = select(Movie).where(Movie.id == id)
        movie = session.exec(statement).first()
        return movie
    except Exception as e:
        logger.error(f"Ошибка при получении фильма по ID {id}: {e}")
        raise


def get_all_movies(session: Session) -> List[Movie]:
    """
    Запрашивает все фильмы из базы.
    
    Args:
        session: сессия базы данных
    
    Returns:
        List[Movie]: Список всех фильмов
    """
    try:
        statement = select(Movie)
        movies = session.exec(statement).all()
        logger.info(f"Получено {len(movies)} фильмов из базы")
        return movies
    except Exception as e:
        logger.error(f"Ошибка при получении всех фильмов: {e}")
        raise


def get_all_movie_titles(session: Session) -> Dict[str, str]:
    """
    Запрашивает названия и описания всех фильмов из базы.
    
    Args:
        session: сессия базы данных
    
    Returns:
        Dict[str, str]: Словарь {название: описание}
    """
    try:
        statement = select(Movie)
        movies = session.exec(statement).all()
        movies_dict = {movie.title: movie.description for movie in movies}
        logger.info(f"Получено {len(movies_dict)} названий фильмов")
        return movies_dict
    except Exception as e:
        logger.error(f"Ошибка при получении названий фильмов: {e}")
        raise


def add_movie(movie: dict, session: Session) -> Tuple[bool, str, Movie]:
    """
    Добавление нового фильма в базу данных.
    
    Args:
        movie: словарь с данными фильма
        session: сессия базы данных
    
    Returns:
        Tuple[bool, str, Movie]: (успех, сообщение, объект фильма)
    """
    # Валидация входных данных
    required_fields = ['title', 'description', 'year', 'genres']
    for field in required_fields:
        if field not in movie:
            raise ValueError(f"Отсутствует обязательное поле: {field}")
    
    # Ограничение длины описания
    movie['description'] = movie['description'][:1000]
    
    # Проверка на дубликаты
    statement = select(Movie).where(
        (Movie.title == movie['title']) & 
        (Movie.year == movie['year'])
    )
    movie_check = session.exec(statement).first()
    if movie_check:
        raise ValueError(f"Фильм с названием '{movie['title']}' и годом выпуска {movie['year']} уже есть в базе")
    
    try:
        defined_movie = Movie(**movie)
        session.add(defined_movie)
        session.commit()
        session.refresh(defined_movie)
        msg = "Фильм успешно добавлен"
        logger.info(f"Фильм '{defined_movie.title}' добавлен в базу")
        return True, msg, defined_movie
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при добавлении фильма: {e}")
        raise


def delete_movie(id: int, session: Session) -> bool:
    """
    Удаление фильма из базы.
    
    Args:
        id: ID фильма для удаления
        session: сессия базы данных
    
    Returns:
        bool: True если фильм удален, False если не найден
    """
    try:
        movie = get_movie_by_id(id, session)
        if movie:
            session.delete(movie)
            session.commit()
            logger.info(f"Фильм '{movie.title}' удален из базы")
            return True
        logger.warning(f"Фильм с ID {id} не найден")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при удалении фильма {id}: {e}")
        raise


def update_movie_database(model: SentenceTransformer, session: Session) -> None:
    """
    Инициализация базы данных фильмов из JSON файлов в директории data.
    
    Args:
        model: модель для генерации эмбеддингов
        session: сессия базы данных
    """
    try:
        # Путь к директории с JSON файлами
        data_dir = Path(__file__).parent.parent / 'data'
        
        if not data_dir.exists():
            raise FileNotFoundError(f"Директория {data_dir} не найдена")
        
        # Находим все JSON файлы в директории
        json_files = list(data_dir.glob('*.json'))
        
        if not json_files:
            raise FileNotFoundError(f"JSON файлы не найдены в директории {data_dir}")
        
        total_added_count = 0
        total_skipped_count = 0
        
        for json_file in json_files:
            logger.info(f"Обрабатываем файл: {json_file.name}")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as file:
                    movie_list = json.load(file)
                
                if not isinstance(movie_list, list):
                    logger.warning(f"Файл {json_file.name} не содержит массив фильмов, пропускаем")
                    continue
                
                # Генерируем эмбеддинги для всех описаний
                desc_list = [movie['description'] for movie in movie_list]
                embedding_list = model.encode(desc_list)
                
                file_added_count = 0
                file_skipped_count = 0
                
                for i, movie_example in enumerate(movie_list):
                    try:
                        movie_example['embedding'] = embedding_list[i].tolist()
                        add_movie(movie_example, session)
                        file_added_count += 1
                    except ValueError as e:
                        # Фильм уже существует
                        logger.info(f"Фильм пропущен: {e}")
                        file_skipped_count += 1
                    except Exception as e:
                        logger.error(f"Ошибка при добавлении фильма {movie_example.get('title', 'Unknown')}: {e}")
                        file_skipped_count += 1
                
                total_added_count += file_added_count
                total_skipped_count += file_skipped_count
                
                logger.info(f"Файл {json_file.name}: добавлено {file_added_count}, пропущено {file_skipped_count} фильмов")
                
            except Exception as e:
                logger.error(f"Ошибка при обработке файла {json_file.name}: {e}")
                continue
        
        logger.info(f"База данных обновлена: всего добавлено {total_added_count}, пропущено {total_skipped_count} фильмов")
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении базы данных фильмов: {e}")
        raise


def search_movies_by_title(title: str, session: Session) -> List[Movie]:
    """
    Поиск фильмов по названию (частичное совпадение).
    
    Args:
        title: часть названия для поиска
        session: сессия базы данных
    
    Returns:
        List[Movie]: Список найденных фильмов
    """
    try:
        statement = select(Movie).where(Movie.title.ilike(f"%{title}%"))
        movies = session.exec(statement).all()
        logger.info(f"Найдено {len(movies)} фильмов по запросу '{title}'")
        return movies
    except Exception as e:
        logger.error(f"Ошибка при поиске фильмов по названию '{title}': {e}")
        raise


def get_movies_by_genre(genre: str, session: Session) -> List[Movie]:
    """
    Получение фильмов по жанру.
    
    Args:
        genre: жанр для поиска
        session: сессия базы данных
    
    Returns:
        List[Movie]: Список фильмов указанного жанра
    """
    try:
        statement = select(Movie).where(Movie.genres.contains([genre]))
        movies = session.exec(statement).all()
        logger.info(f"Найдено {len(movies)} фильмов жанра '{genre}'")
        return movies
    except Exception as e:
        logger.error(f"Ошибка при поиске фильмов по жанру '{genre}': {e}")
        raise
