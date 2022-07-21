"use strict";
var entry_url;

function json_post_sender(action, data, handler, response_type=""){
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
    xhttp_request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhttp_request.send(data);
}

function go_back_entry(){
    window.location.assign(entry_url)
}

function mix_audio_response_handler(xhttp_request){
    let blob_url = URL.createObjectURL(xhttp_request.response)
    document.getElementById("audio_waiting_hint").hidden = true;
    document.getElementById("mixed_audio_ctrlr").src = blob_url;
    document.getElementById("mixed_audio_ctrlr").hidden = false;
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
        json_post_sender("/second/mix_audio", data, mix_audio_response_handler, "blob");
    }
}

function start(){
    document.getElementById("get_mixed_audio_btn").addEventListener("click", get_mixed_audio_btn_clicked)
}

window.onload = start