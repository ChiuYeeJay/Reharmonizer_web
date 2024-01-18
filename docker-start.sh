rabbitmq-server >& ./rabbitmq.log &
celery -A celery_tasks worker --loglevel=INFO >& ./celery.log &
python3.9 auto_tempfile_cleaner.py &
gunicorn -b 0.0.0.0:8000 --timeout 120 app:app