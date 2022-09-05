import celery
import audio2midi_modified as audio2midi
import audioread.ffdec

LOCAL_TEMPFILE_PATH = "tempfiles/"

celery_app = celery.Celery('celery_tasks', backend='rpc://', broker='pyamqp://guest@localhost//')

@celery_app.task
def audio2midi_background(workspace_path):
    # In order to avoid exception in audio2midi.run(), using audioread directly.
    audioread_obj = audioread.ffdec.FFmpegAudioFile(workspace_path+'/origin.wav')
    audio2midi.run(audioread_obj, workspace_path+'/melody.mid')