FROM python:3.9-slim
EXPOSE 8000
WORKDIR /app
COPY ./requirements.txt ./
RUN ["apt", "update"]
RUN ["apt", "install", "python3", "pip", "ffmpeg", "libsndfile1", "gunicorn", "rabbitmq-server", "--yes"]
RUN ["pip", "install", "-r", "requirements.txt"]
COPY ./ ./
ENTRYPOINT [ "/bin/bash", "./docker-start.sh" ]
