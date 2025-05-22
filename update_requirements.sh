#!/bin/bash

# Активировать виртуальное окружение
echo "Activating the virtual environment..."
source .venv/bin/activate

# Проверка успешности активации
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Cannot activate the virtual environment."
    exit 1
fi

echo "Virtual environment activated."

# Обновление основного файла зависимостей
echo "Compiling pyproject.toml to requirements.txt..."
pip-compile --resolver=backtracking pyproject.toml
if [ $? -ne 0 ]; then
    echo "Error while compiling pyproject.toml"
    exit 1
fi
echo "The main requirements file updated."

# Обновление файла зависимостей для разработки
echo "Compiling pyproject.toml (with dev requirements) to requirements.dev.txt..."
pip-compile --extra=dev --resolver=backtracking pyproject.toml --output-file=requirements.dev.txt
if [ $? -ne 0 ]; then
    echo "Error while compiling pyproject.toml for development"
    exit 1
fi
echo "The development requirements file updated."

# Синхронизация окружения с файлом зависимостей для разработки
echo "Synchronizing the environment with requirements.dev.txt..."
pip-sync requirements.dev.txt
if [ $? -ne 0 ]; then
    echo "Error synchronizing requirements."
    exit 1
fi
echo "Virtual environment synchronized."

echo "All operations completed successfully!"

# deactivate
