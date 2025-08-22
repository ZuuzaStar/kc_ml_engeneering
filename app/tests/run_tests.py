#!/usr/bin/env python3
"""
Скрипт для запуска unit-тестов системы рекомендаций фильмов
"""

import subprocess
import sys
import os

def run_tests():
    """Запускает все тесты"""
    print("🚀 Запуск unit-тестов для системы рекомендаций фильмов")
    print("=" * 60)
    
    # Переходим в директорию app
    app_dir = os.path.dirname(os.path.abspath(__file__)).replace('/tests', '')
    os.chdir(app_dir)
    
    # Устанавливаем переменную окружения для тестов
    os.environ["TESTING"] = "true"
    
    try:
        # Запускаем pytest из директории tests
        result = subprocess.run([
            "python", "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True)
        
        # Выводим результат
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  Предупреждения:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Все тесты прошли успешно!")
        else:
            print(f"\n❌ Тесты завершились с ошибками (код: {result.returncode})")
            
        return result.returncode
        
    except FileNotFoundError:
        print("❌ pytest не найден. Установите его командой:")
        print("   pip install -r tests/requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Ошибка при запуске тестов: {e}")
        return 1

def run_specific_test(test_path):
    """Запускает конкретный тест"""
    print(f"🚀 Запуск теста: {test_path}")
    print("=" * 60)
    
    # Переходим в директорию app
    app_dir = os.path.dirname(os.path.abspath(__file__)).replace('/tests', '')
    os.chdir(app_dir)
    
    try:
        result = subprocess.run([
            "python", "-m", "pytest", 
            test_path, 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  Предупреждения:")
            print(result.stderr)
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Ошибка при запуске теста: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Запуск конкретного теста
        test_path = sys.argv[1]
        exit_code = run_specific_test(test_path)
    else:
        # Запуск всех тестов
        exit_code = run_tests()
    
    sys.exit(exit_code)