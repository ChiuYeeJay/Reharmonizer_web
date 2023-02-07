#!/bin/bash
# Program: 
#   This program will starts reharmonizer web server.
#   To fully stop it:
#       ps and find tempfile_folder_cleaner and kill it
#       ps and find gunicorn and kill it
#       ps and find celery and kill it
#       execute rabbitmqctl stop

/usr/local/sbin/rabbitmq-server &
celery -A celery_tasks worker --loglevel=INFO &
gunicorn app:app &
python3 auto_tempfile_cleaner.py &