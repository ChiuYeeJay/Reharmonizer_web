FROM python:3.9.16-slim
EXPOSE 8000
WORKDIR /app
COPY ./requirements.txt ./
RUN ["pip", "install", "-r", "requirements.txt"]
RUN ["apt", "update"]
RUN ["apt", "install", "ffmpeg", "libsndfile1", "gunicorn", "--yes"]
COPY ./ ./
ENTRYPOINT [ "gunicorn", "app:app", "-b", "0.0.0.0:8000", "--timeout", "120"] 
