toir_atu_fastapi


Порядок запуска:

Cоздать и активировать виртуальное окружение:  
```  
python -m venv venv  
```  

* на Linux/macOS
```  
source venv/bin/activate
```

* на windows  
```  
source venv/scripts/activate  
```  

Установить зависимости из файла requirements.txt:  
```  
python -m pip install --upgrade pip  
```  

```  
pip install -r requirements.txt  
```  

Создать файл .env в корне проекта с переменными окружения (есть в env.example):  

 
Автоматическое создание файла миграций:
```alembic revision --autogenerate -m "First migration"```

Применение миграций:
```alembic upgrade head```

Запуск приложения через терминал:
```uvicorn toir_app.main:toir_app --host 0.0.0.0 --port 8000 --reload```
