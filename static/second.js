"use strict";

function post_sender(action, data, handler, content_type="application/json", response_type=""){
    let xhttp_request = new XMLHttpRequest();
    xhttp_request.onreadystatechange = ()=>{
        if (xhttp_request.readyState != XMLHttpRequest.DONE) return;
        if (xhttp_request.status !== 200) {
            console.warn("something wrong in " + action + ": " + xhttp_request.status);
            return;
        }

        handler(xhttp_request)
    }
    xhttp_request.open("POST", action);
    xhttp_request.responseType = response_type
    xhttp_request.setRequestHeader("Content-Type", content_type+";charset=UTF-8");
    xhttp_request.send(data);
}

function go_back_entry(){
    window.location.assign("/")
}

function mix_audio_response_handler(xhttp_request){
    // console.log(xhttp_request.response)
    let blob_url = URL.createObjectURL(xhttp_request.response)
    document.getElementById("audio_waiting_hint").hidden = true;
    document.getElementById("mixed_audio_ctrlr").src = blob_url;
    document.getElementById("mixed_audio_ctrlr").hidden = false;
    document.getElementById("dl_mixed_audio_link").href = blob_url;
}

function get_mixed_audio_btn_clicked(){
    document.getElementById("audio_waiting_hint").hidden = false;
    document.getElementById("mixed_audio_ctrlr").hidden = true;
    let original_checked = document.getElementById("original_audio_checkbox").checked;
    let melody_checked = document.getElementById("melody_audio_checkbox").checked;
    let harmony_checked = document.getElementById("harmony_audio_checkbox").checked;
    let checked_list = [original_checked, melody_checked, harmony_checked];
    if(checked_list == [false, false, false]){
        alert("check at least one!");
    }
    else{
        let data = JSON.stringify({"would_be_combined":checked_list})
        post_sender("/second/mix_audio", data, mix_audio_response_handler, "application/json", "blob");
    }
}

function request_midi_dowload_link(){
    post_sender("/second/get_midi_file", "melody", function(xhttp_request){
        let blob_url = URL.createObjectURL(xhttp_request.response)
        document.getElementById("melody_midi_dl_link").href = blob_url;
    }, "text/plain", "blob");

    post_sender("/second/get_midi_file", "harmony", function(xhttp_request){
        let blob_url = URL.createObjectURL(xhttp_request.response)
        document.getElementById("harmony_midi_dl_link").href = blob_url;
    }, "text/plain", "blob");
}

function request_chords(){
    post_sender("/second/get_chords", "", function(xhttp_request){
        document.getElementById("chord_list").innerText = xhttp_request.response;
    }, "text/plain", "text");
}

function request_harmonizing_again(){
    document.getElementById("regenerate_hint").hidden = false;
    post_sender("/second/hamonize_again", JSON.stringify({"octave":4}), function(xhttp_request){
        get_mixed_audio_btn_clicked();
        request_midi_dowload_link();
        request_chords();
        document.getElementById("regenerate_hint").hidden = true;
    }, "text/plain", "text")
}

function start(){
    document.getElementById("get_mixed_audio_btn").addEventListener("click", get_mixed_audio_btn_clicked);
    document.getElementById("back_last_page_btn").addEventListener("click", go_back_entry);
    document.getElementById("regenerate_harmony").addEventListener("click", request_harmonizing_again);
    get_mixed_audio_btn_clicked();
    request_midi_dowload_link();
    request_chords();
}

window.onload = start