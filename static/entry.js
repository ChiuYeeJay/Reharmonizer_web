"use strict";

var audio_id = ""

function post_sender(action, data, handler, content_type="", response_type=""){
    let xhttp_request = new XMLHttpRequest();
    xhttp_request.onreadystatechange = ()=>{
        if (xhttp_request.readyState != XMLHttpRequest.DONE) return;
        if (xhttp_request.status !== 200) {
            console.warn("something wrong in " + action + ": " + xhttp_request.status);
            window.alert("something wrong: " + xhttp_request.status)
            return;
        }

        handler(xhttp_request)
    }
    xhttp_request.open("POST", action);
    if(response_type != "") xhttp_request.responseType = response_type
    if(content_type != "") xhttp_request.setRequestHeader("Content-Type", content_type+";charset=UTF-8");
    xhttp_request.send(data);
}

function harmonization_suceed(xhttp_request){
    document.getElementById("upload_status").innerText = "redirect..."
    window.location.assign(xhttp_request.responseText)
}

function start_harmonization(){
    let harmonization_data = JSON.stringify({"args":{"octave":4}, "audio_id":audio_id});
    post_sender("/harmonize", harmonization_data, harmonization_suceed, 
        "application/json", "text");
}

function audio2midi_suceeded(xhttp_request){
    document.getElementById("upload_status").innerText = "harmonizing..."
    start_harmonization()
}

function start_audio2midi(){
    post_sender("/audio2midi", JSON.stringify({"audio_id":audio_id}), audio2midi_suceeded,
                "application/json")
}

function submit_suceeded(xhttp_request){
    audio_id = xhttp_request.response.audio_id;
    console.log("audio_id: " + audio_id)
    document.getElementById("upload_status").innerText = "processing audio..."
    start_audio2midi()
}

function submit_audio(){
    let form_element = document.getElementById("audio_form")
    form_element.hidden = true;
    document.getElementById("upload_status").innerText = "uploading audio..."
    
    post_sender(form_element.action, new FormData(form_element), submit_suceeded, "", "json");
}

function on_audio_chosen(){
    let submit_btn_element = document.getElementById("submit_btn");
    let fileinput_element = document.getElementById("audio_upload");
    if(fileinput_element.value == "") return;
    submit_btn_element.disabled = true;
    let url = URL.createObjectURL(fileinput_element.files[0]);
    let audio = new Audio(url);
    audio.oncanplaythrough = ()=>{
        // console.log(audio.duration);
        if(audio.duration > 180){
            alert("audio length too long, it must be less then 180s")
            return;
        }
        document.getElementById("submit_btn").disabled = false;
    }
}

window.onload = on_audio_chosen;