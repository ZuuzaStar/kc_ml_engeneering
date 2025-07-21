import os
from catboost import CatBoostClassifier

def get_model_path(path: str) -> str:
    if os.environ.get("IS_LMS") == "1":  # проверяем где выполняется код в лмс, или локально. Немного магии
        MODEL_PATH = '/workdir/user_input/model'
    else:
        MODEL_PATH = path
    return MODEL_PATH

def load_models():
    # Используем функцию get_model_path для корректного определения пути
    model_path = get_model_path("/my/super/path/catboost_model.cbm")  # Указываем только имя файла
    
    # Загружаем модель CatBoost
    model = CatBoostClassifier()
    model.load_model(model_path)
    
    return model