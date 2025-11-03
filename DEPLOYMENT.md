# Руководство по развертыванию на Yandex Cloud

## Предварительные требования

На сервере должны быть установлены:
- Docker
- Docker Compose
- Nginx (уже установлен, но будет использоваться контейнерная версия)
- Git (опционально, для обновлений)

## Шаг 1: Подготовка сервера

### 1.1 Подключение к серверу
```bash
ssh username@your-server-ip
```

### 1.2 Создание директории для проекта
```bash
mkdir -p /opt/tasktracker
cd /opt/tasktracker
```

## Шаг 2: Клонирование проекта

### Вариант 1: Через Git
```bash
git clone <repository-url> .
```

### Вариант 2: Загрузка файлов вручную
```bash
# С локального компьютера
scp -r /Users/lvv/PycharmProjects/SkyPro-Graduation-Project-tracker/* username@your-server-ip:/opt/tasktracker/
```

## Шаг 3: Настройка переменных окружения

### 3.1 Создание .env файла
```bash
cd /opt/tasktracker
cp .env.production.example .env
nano .env
```

### 3.2 Заполните следующие параметры:
```env
# Django settings
SECRET_KEY=<сгенерируйте длинный случайный ключ>
DEBUG=False
ALLOWED_HOSTS=<IP-адрес-вашего-сервера>

# Database settings
POSTGRES_DB=tasktracker_prod
POSTGRES_USER=tasktracker_user
POSTGRES_PASSWORD=<сильный-пароль-для-БД>
POSTGRES_HOST=db
POSTGRES_PORT=5432

# CSRF settings
CSRF_TRUSTED_ORIGINS=http://<IP-адрес-вашего-сервера>
```

### 3.3 Генерация SECRET_KEY
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Шаг 4: Остановка системного Nginx (если используется)

Если на сервере запущен системный Nginx на порту 80:
```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

## Шаг 5: Запуск приложения

### 5.1 Первое развертывание
```bash
chmod +x deploy.sh
./deploy.sh
```

### 5.2 Проверка статуса контейнеров
```bash
docker-compose -f docker-compose.production.yml ps
```

Все контейнеры должны быть в статусе "Up".

## Шаг 6: Создание суперпользователя

```bash
docker-compose -f docker-compose.production.yml exec web python manage.py createsuperuser
```

Введите:
- Email
- Пароль

## Шаг 7: Проверка работы

### 7.1 Откройте в браузере
```
http://<IP-адрес-вашего-сервера>/admin/
```

### 7.2 Проверка логов
```bash
# Все логи
docker-compose -f docker-compose.production.yml logs -f

# Только Django
docker-compose -f docker-compose.production.yml logs -f web

# Только Nginx
docker-compose -f docker-compose.production.yml logs -f nginx

# Только БД
docker-compose -f docker-compose.production.yml logs -f db
```

## Полезные команды

### Остановка приложения
```bash
docker-compose -f docker-compose.production.yml down
```

### Запуск приложения
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Перезапуск приложения
```bash
docker-compose -f docker-compose.production.yml restart
```

### Обновление после изменений кода
```bash
./deploy.sh
```

### Просмотр логов
```bash
docker-compose -f docker-compose.production.yml logs -f
```

### Выполнение команд Django
```bash
# Миграции
docker-compose -f docker-compose.production.yml exec web python manage.py migrate

# Создание суперпользователя
docker-compose -f docker-compose.production.yml exec web python manage.py createsuperuser

# Django shell
docker-compose -f docker-compose.production.yml exec web python manage.py shell

# Сбор статики
docker-compose -f docker-compose.production.yml exec web python manage.py collectstatic --noinput
```

### Резервное копирование базы данных
```bash
# Создание бэкапа
docker-compose -f docker-compose.production.yml exec db pg_dump -U tasktracker_user tasktracker_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
docker-compose -f docker-compose.production.yml exec -T db psql -U tasktracker_user tasktracker_prod < backup_file.sql
```

### Очистка Docker ресурсов
```bash
# Удаление неиспользуемых образов
docker image prune -a

# Удаление неиспользуемых volumes
docker volume prune
```

## Решение проблем

### Проблема: Контейнер web не запускается
```bash
# Проверьте логи
docker-compose -f docker-compose.production.yml logs web

# Проверьте .env файл
cat .env
```

### Проблема: База данных недоступна
```bash
# Проверьте статус БД
docker-compose -f docker-compose.production.yml exec db pg_isready -U tasktracker_user

# Проверьте логи БД
docker-compose -f docker-compose.production.yml logs db
```

### Проблема: Nginx возвращает 502
```bash
# Проверьте, что web контейнер запущен
docker-compose -f docker-compose.production.yml ps web

# Проверьте логи nginx
docker-compose -f docker-compose.production.yml logs nginx
```

### Проблема: Static файлы не отдаются
```bash
# Пересоберите статику
docker-compose -f docker-compose.production.yml exec web python manage.py collectstatic --noinput --clear
```

## Мониторинг

### Проверка использования ресурсов
```bash
docker stats
```

### Проверка дискового пространства
```bash
df -h
docker system df
```

## Обновление проекта

### Если используется Git
```bash
cd /opt/tasktracker
git pull
./deploy.sh
```

### Если файлы загружаются вручную
```bash
# С локального компьютера загрузите изменения
scp -r /Users/lvv/PycharmProjects/SkyPro-Graduation-Project-tracker/* username@your-server-ip:/opt/tasktracker/

# На сервере
cd /opt/tasktracker
./deploy.sh
```

## Безопасность

### Рекомендации:
1. Используйте сильные пароли для БД
2. Регулярно обновляйте Docker образы
3. Настройте firewall (ufw):
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw enable
   ```
4. Настройте автоматические бэкапы БД
5. Мониторьте логи на наличие ошибок

## Автоматизация

### Настройка автоматического бэкапа (cron)
```bash
# Создайте скрипт
nano /opt/tasktracker/backup.sh
```

Содержимое backup.sh:
```bash
#!/bin/bash
cd /opt/tasktracker
docker-compose -f docker-compose.production.yml exec -T db pg_dump -U tasktracker_user tasktracker_prod > /opt/backups/backup_$(date +%Y%m%d_%H%M%S).sql
# Удалить бэкапы старше 30 дней
find /opt/backups -name "backup_*.sql" -mtime +30 -delete
```

Добавьте в cron:
```bash
chmod +x /opt/tasktracker/backup.sh
crontab -e

# Добавьте строку (бэкап каждый день в 3:00)
0 3 * * * /opt/tasktracker/backup.sh
```
