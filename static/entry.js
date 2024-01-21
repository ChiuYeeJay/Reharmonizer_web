"use strict";

var audio_id = "";
var audio2midi_asking_interval = 2000;
var harmonize_asking_interval = 1000;
var final_progress_stage = 3;

var accepted_file_extension = ["3gp", "aa", "aac", "aax", "act", "aiff", "alac", "amr",
                               "ape", "au", "awb", "dss", "dvf", "flac", "gsm", "iklax",
                               "ivs", "m4a", "m4b", "m4p", "mmf", "movpkg", "mp3", "mpc",
                               "msv", "nmf", "ogg", "oga", "mogg", "opus", "ra", "rm", "raw",
                               "rf64", "sln", "tta", "voc", "vox", "wav", "wma", "wv", "webm", "8svx", "cda"];

function post_sender(action, data, handler, content_type="", response_type=""){
    let xhttp_request = new XMLHttpRequest();
    xhttp_request.onreadystatechange = ()=>{
        if (xhttp_request.readyState != XMLHttpRequest.DONE) return;
        if (xhttp_request.status !== 200) {
            console.warn("something wrong in " + action + ": " + xhttp_request.status);
            window.alert("something wrong: " + xhttp_request.status);
            return;
        }

        handler(xhttp_request);
    }
    xhttp_request.open("POST", action);
    if(response_type != "") xhttp_request.responseType = response_type;
    if(content_type != "") xhttp_request.setRequestHeader("Content-Type", content_type+";charset=UTF-8");
    xhttp_request.send(data);
}

function set_processing_progress(stage){
    document.getElementById("prcessing_progress").style.display = "flex";
    for(let i=0;i<stage;i++){
        document.getElementById("progress_"+i).style.backgroundColor = "rgba(131, 233, 122, 0.3)";
        document.getElementById("progress_"+i).style.animation = "";
    }
    if(stage < final_progress_stage){
        document.getElementById("progress_"+stage).style.animation = "progress_breath 1s infinite alternate linear"
    }
    else{
        document.getElementById("progress_"+stage).style.backgroundColor = "rgba(131, 233, 122, 0.3)";
    }
}

function ask_whether_harmonize_completed(){
    post_sender("/whether_harmonize_completed", JSON.stringify({"audio_id":audio_id, "lang":document.body.lang}), (xhttp_request)=>{
        if(xhttp_request.response.status){
            set_processing_progress(3);
            window.location.assign(xhttp_request.response.second_url);
        }
        else{
            setTimeout(ask_whether_harmonize_completed, harmonize_asking_interval);
        }
    }, "application/json", "json");
}

function start_harmonization(){
    let harmonization_data = JSON.stringify({"args":{"octave":4}, "audio_id":audio_id});
    post_sender("/harmonize", harmonization_data, ask_whether_harmonize_completed, 
        "application/json", "text");
}

function ask_whether_audio2midi_completed(){
    post_sender("/whether_audio2midi_completed", JSON.stringify({"audio_id":audio_id}), (xhttp_request)=>{
        if(xhttp_request.response.status){
            set_processing_progress(2);
            start_harmonization();
        }
        else{
            setTimeout(ask_whether_audio2midi_completed, audio2midi_asking_interval);
        }
    }, "application/json", "json");
}

function start_audio2midi(){
    post_sender("/audio2midi", JSON.stringify({"audio_id":audio_id}), 
                (xhttp_request)=>{ask_whether_audio2midi_completed();}, "application/json");
}

function submit_suceeded(xhttp_request){
    audio_id = xhttp_request.response.audio_id;
    console.log("audio_id: " + audio_id);
    set_processing_progress(1);
    start_audio2midi();
}

function submit_audio(file){
    document.getElementById("audio_form").style.display = "none";
    document.getElementById("after_uplaod").style.display = "flex"
    document.getElementById("uplaoded_audio_name").innerText = file.name;
    set_processing_progress(0);

    let formdata = new FormData();
    formdata.append("original_audio", file);
    post_sender("/upload", formdata, submit_suceeded, "", "json");            
    // post_sender(form_element.action, new FormData(form_element), submit_suceeded, "", "json");
}

function check_audio(file){
    let url = URL.createObjectURL(file);
    let audio = new Audio(url);
    audio.oncanplaythrough = ()=>{
        // console.log(audio.duration);
        if(audio.duration > 180){
            alert("audio length too long, it must be less then 180s");
        }
        else{
            submit_audio(file);
        }
    }
}

function on_audio_chosen(){
    let fileinput_element = document.getElementById("audio_upload");
    if(fileinput_element.value == "") return;
    check_audio(fileinput_element.files[0]);
}

function drop_handler(event){
    event.preventDefault();
    document.getElementById("drag_and_drop").style.backgroundColor = "transparent";
    let file;
    if (event.dataTransfer.items) {
        let item = event.dataTransfer.items[0];
        if(item.kind === "file"){
            file = item.getAsFile();
        }
    } else {
        file = event.dataTransfer.files[0];
    }
    // console.log(file);

    let fileExt = file.name.split('.').pop().toLowerCase();
    let flag = false;
    for(let i=0;i<accepted_file_extension.length;i++){
        if(fileExt === accepted_file_extension[i]){
            flag = true;
        }
    }
    if(!flag){
        alert("format not accepted. (accepted: wav, mp3, m4a, flac, mp4, wma, aac)");
        return;
    }
    
    check_audio(file);
}

function dragover_handler(event){
    event.preventDefault();
    document.getElementById("drag_and_drop").style.backgroundColor = "rgba(255,255,255,0.1)";
}

function dragleave_handler(event){
    document.getElementById("drag_and_drop").style.backgroundColor = "transparent";
}