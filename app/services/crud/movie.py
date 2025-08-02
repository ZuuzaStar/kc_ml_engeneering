from models.movie import Movie

def change_title(movie: Movie, new_title: str):
        """Возможность исправлять ошибки в названии"""
        if len(new_title) < 1:
            raise ValueError("Название фильма должно быть не короче одного символа")
        movie.title = new_title
    
def change_description(movie: Movie, new_description: str):
    """Возможность исправлять ошибки в описании"""
    if len(new_description) < 10:
        raise ValueError("Описание фильма не должно быть короче 10 символов")
    movie.description = new_description