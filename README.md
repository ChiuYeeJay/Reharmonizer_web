# Reharmonizer_web

Reharmonizer_web is a web app that allows people upload random audio, and generate piano melody and harmony using the concept of unfunctional harmony.

## Dependencies

- Python 3.9 or higher
- Python Libraries (listed in requirements.txt)
- [RabbitMQ](https://www.rabbitmq.com/download.html)
- libsndfile1
- ffmpeg

## Installation and Run

1. Clone this repository and cd to it
2. Install all dependancies
3. Run RabbitMQ server
4. Run celery worker (you can use `celery -A celery_tasks worker --loglevel=INFO`)
5. Run `auto_tempfile_cleaner.py` to automatically clean storage (optional)
6. Run `gunicorn -b 0.0.0.0:80 app:app`
7. Open yor browser and upload your audio

## Piano Sound
The piano sound is extracted and modified from [YDP-GrandPiano](https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html) soundfont.


## Docker
Docker Hub:
[t41372/reharmonizer_web_docker](https://hub.docker.com/repository/docker/t41372/reharmonizer_web_docker/)


Pull from docker hub and run image
~~~ sh
docker run -d -p 8000:8000 --name Reharmonizer_web t41372/reharmonizer_web_docker:latest
~~~

Build image locally
~~~ shell
docker build -t reharmonizer_web_docker .
~~~

or build images for multiple archetectures with buildx
~~~ shell
docker buildx build \
    -t reharmonizer_web_docker:latest \
    --platform linux/amd64,linux/arm64 \
    .
~~~
