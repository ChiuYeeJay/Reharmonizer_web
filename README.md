# Reharmonizer_web

Reharmonizer_web is a web app that allows people upload random audio, and generate piano melody and harmony using the concept of unfunctional harmony.

## Dependencies

- Python Libraries (listed in requirements.txt)
- [RabbitMQ](https://www.rabbitmq.com/download.html)
- libsndfile1
- ffmpeg

## Installation and Run

1. Clone this repository and cd to it
2. Install all dependancies
3. Run RabbitMQ server
4. Run celery worker (you can using `celery -A celery_tasks worker --loglevel=INFO`)
5. Run `gunicorn -b 0.0.0.0:80 app:app`
6. Open yor browser and upload your audio

## Piano Sound

The piano sound is extracted and modified from [YDP-GrandPiano](https://freepats.zenvoid.org/Piano/acoustic-grand-piano.html) soundfont.