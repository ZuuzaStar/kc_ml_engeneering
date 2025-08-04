from models.movie import Movie
from sqlmodel import Session

def change_title(movie: Movie, new_title: str, session:Session):
        """Возможность исправлять ошибки в названии"""
        if len(new_title) < 1:
            raise ValueError("Название фильма должно быть не короче одного символа")
        movie.title = new_title
        try:
            session.add(movie)
            session.commit()
            session.refresh(movie)
            return movie
        except Exception as e:
            session.rollback()
            raise
    
def change_description(movie: Movie, new_description: str, session:Session):
    """Возможность исправлять ошибки в описании"""
    if len(new_description) < 10:
        raise ValueError("Описание фильма не должно быть короче 10 символов")
    movie.description = new_description
    try:
        session.add(movie)
        session.commit()
        session.refresh(movie)
        return movie
    except Exception as e:
        session.rollback()
        raise