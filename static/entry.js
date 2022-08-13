"use strict";

var audio_id = ""

function harmonization_suceed(){
    if (this.readyState != XMLHttpRequest.DONE) return;
    if (this.status === 200) {
        document.getElementById("upload_status").innerText = "redirect..."
        window.location.assign(this.responseText)
    }
    else{
        console.warn("something wrong: " + this.status);
        window.alert("something wrong: " + this.status)
    }
}

function start_harmonization(){
    let harmonization_args = {"octave":4}
    let harmonization_request = new XMLHttpRequest();
    harmonization_request.onreadystatechange = harmonization_suceed
    harmonization_request.open("POST", "/harmonize");
    harmonization_request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    harmonization_request.send(JSON.stringify({"args":harmonization_args, "audio_id":audio_id}));
}

function audio2midi_suceeded(){
    if (this.readyState != XMLHttpRequest.DONE) return;
    if (this.status === 200) {
        document.getElementById("upload_status").innerText = "harmonizing..."
        start_harmonization()
    }
    else{
        console.warn("something wrong: " + this.status);
        window.alert("something wrong: " + this.status)
    }
}

function start_audio2midi(){
    let audio2midi_request = new XMLHttpRequest();
    audio2midi_request.onreadystatechange = audio2midi_suceeded
    audio2midi_request.open("POST", "/audio2midi");
    audio2midi_request.setRequestHeader("Content-Type", "application/json;charset=UTF-8")
    audio2midi_request.send(JSON.stringify({"audio_id":audio_id}));
}

function submit_suceeded(){
    if (this.readyState != XMLHttpRequest.DONE) return;
    if (this.status === 200) {
        // console.log(this.responseText);
        audio_id = this.response.audio_id;
        console.log("audio_id: " + audio_id)
        document.getElementById("upload_status").innerText = "processing audio..."
        start_audio2midi()
    }
    else{
        console.warn("something wrong: " + this.status);
        window.alert("something wrong: " + this.status)
    }
}

function submit_audio(){
    let form_element = document.getElementById("audio_form")
    form_element.hidden = true;
    document.getElementById("upload_status").innerText = "uploading audio..."
    
    let audio_submit_request = new XMLHttpRequest();
    audio_submit_request.onreadystatechange = submit_suceeded
    audio_submit_request.open("POST", form_element.action);
    audio_submit_request.responseType = "json"
    audio_submit_request.send(new FormData(form_element));
}