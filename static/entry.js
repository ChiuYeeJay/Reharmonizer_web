"use strict";
var audio_submit_request;
var audio2midi_request;

function audio2midi_suceeded(){
    if (audio2midi_request.readyState != XMLHttpRequest.DONE) return;
    if (audio2midi_request.status === 200) {
        document.getElementById("upload_status").innerText = "redirect..."
        window.location.assign(audio2midi_request.responseText)
    }
    else{
        console.warn("something wrong: " + audio2midi_request.status);
    }
}

function start_audio2midi(){
    audio2midi_request = new XMLHttpRequest();
    audio2midi_request.onreadystatechange = audio2midi_suceeded
    audio2midi_request.open("POST", "/audio2midi");
    audio2midi_request.send();
}

function submit_suceeded() {
    if (audio_submit_request.readyState != XMLHttpRequest.DONE) return;
    if (audio_submit_request.status === 200) {
        // console.log(audio_submit_request.responseText);
        document.getElementById("upload_status").innerText = "processing audio..."
        start_audio2midi()
    }
    else{
        console.warn("something wrong: " + audio_submit_request.status);
    }
}

function submit_audio () {
    let form_element = document.getElementById("audio_form")
    form_element.hidden = true;
    document.getElementById("upload_status").innerText = "uploading audio..."
    audio_submit_request = new XMLHttpRequest();
    audio_submit_request.onreadystatechange = submit_suceeded
    audio_submit_request.open("POST", form_element.action);
    audio_submit_request.send(new FormData(form_element));
}