# Reharmonizer_web

Reharmonizer_web is a web app that allows people upload random audio, and generate piano melody and harmony using the concept of unfunctional harmony.

## Dependencies

- Python Library
  - pydub
  - numpy
  - librosa
  - midiutil
  - mido

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

