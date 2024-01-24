"use strict";

var audio_id = "";
var hamonize_again_asking_interval = 1000;
var mix_audio_asking_interval = 1000;
var checkbox_status = [true, true, true];
var checkbox_num_to_id = ["original_audio_checkbox", "melody_audio_checkbox", "harmony_audio_checkbox"];

function get_and_validate_audio_id(){
    let url_param = new URLSearchParams(window.location.search);
    if(url_param.has("audio_id")){
        audio_id = url_param.get("audio_id");
        console.log("audio_id: " + audio_id);
        post_sender("/second/validate_audio_id", JSON.stringify({"audio_id":audio_id}), start, 
                    "application/json", "json");
    }
    else{
        go_back_entry();
    }
}

// after audio_id being validated, initialze buttons callback and send first requests
// called by handler of 'get_and_validate_audio_id'
function start(xhttp_request){
    if(!xhttp_request.response.is_valid){
        go_back_entry();
    }
    document.getElementById("get_mixed_audio_btn").addEventListener("click", get_mixed_audio_btn_clicked);
    document.getElementById("back_last_page_btn").addEventListener("click", go_back_entry);
    document.getElementById("regenerate_harmony").addEventListener("click", request_harmonizing_again);
    document.getElementById("regenerate_harmony_on_panel").addEventListener("click", regenerate_harmony_btn_on_panel_clicked);
    get_mixed_audio_btn_clicked();
    request_midi_dowload_link();
    request_chords();
    refresh_arg_value_display();

    if(document.body.lang == "zh-tw"){
        document.getElementById("lang_link").href = "/second/en?audio_id=" + audio_id;
    }
    else{
        document.getElementById("lang_link").href = "/second?audio_id=" + audio_id;       
    }
}

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

function go_back_entry(){
    if(document.body.lang == "en"){
        window.location.assign("/en");
    }
    else{
        window.location.assign("/");
    }
}

function ask_whether_mix_audio_completed(last_mtime, would_be_combined){
    let data = JSON.stringify({"audio_id":audio_id, "last_mtime":last_mtime, "would_be_combined":would_be_combined});
    post_sender("/second/whether_mix_audio_completed", data, (xhttp_request)=>{
        if(xhttp_request.response.size != 0){
            let blob_url = URL.createObjectURL(xhttp_request.response);
            document.getElementById("audio_waiting_hint").hidden = true;
            document.getElementById("mixed_audio_ctrlr").src = blob_url;
            document.getElementById("mixed_audio_ctrlr").hidden = false;
            document.getElementById("dl_mixed_audio_link").href = blob_url;
        }
        else{
            setTimeout(()=>{ask_whether_mix_audio_completed(last_mtime, would_be_combined)}, mix_audio_asking_interval);
        }
    }, "application/json", "blob");
}

function get_mixed_audio_btn_clicked(){
    if(!(checkbox_status[0] || checkbox_status[1] || checkbox_status[2])){
        alert("Check at least one, or it would be silent!");
        return;
    }
    document.getElementById("audio_waiting_hint").hidden = false;
    document.getElementById("mixed_audio_ctrlr").hidden = true;
    let data = JSON.stringify({"would_be_combined":checkbox_status, "audio_id":audio_id});
    post_sender("/second/mix_audio", data, (xhttp_request)=>{
        ask_whether_mix_audio_completed(xhttp_request.response.last_mtime, checkbox_status);
    }, "application/json", "json");
}

function checkbox_clicked(ev,num){
    let target = document.getElementById(checkbox_num_to_id[num]);
    checkbox_status[num] = !checkbox_status[num];
    if(checkbox_status[num]){
        target.style.backgroundColor = "rgba(0, 153, 3, 0.855)";
        target.children[0].hidden = false;
        target.children[1].hidden = true;
    }
    else{
        target.style.backgroundColor = "transparent";
        target.children[0].hidden = true;
        target.children[1].hidden = false;
    }
}

function request_midi_dowload_link(){
    let melody_data = JSON.stringify({"which_midi":"melody", "audio_id":audio_id});
    post_sender("/second/get_midi_file", melody_data, function(xhttp_request){
        let blob_url = URL.createObjectURL(xhttp_request.response);
        document.getElementById("melody_midi_dl_link").href = blob_url;
    }, "application/json", "blob");

    let harmony_data = JSON.stringify({"which_midi":"harmony", "audio_id":audio_id})
    post_sender("/second/get_midi_file", harmony_data, function(xhttp_request){
        let blob_url = URL.createObjectURL(xhttp_request.response);
        document.getElementById("harmony_midi_dl_link").href = blob_url;
    }, "application/json", "blob");
}

function request_chords(){
    post_sender("/second/get_chords", JSON.stringify({"audio_id":audio_id}), function(xhttp_request){
        document.getElementById("chord_list").innerText = xhttp_request.response;
    }, "application/json", "text");
}

function ask_whether_harmonize_again_completed(last_mtime){
    post_sender("/whether_harmonize_again_completed", 
        JSON.stringify({"audio_id":audio_id, "last_mtime":last_mtime}), 
        (xhttp_request)=>{
            if(xhttp_request.response.status){
                get_mixed_audio_btn_clicked();
                request_midi_dowload_link();
                request_chords();
                document.getElementById("regenerate_hint_panel").hidden = true;
            }
            else{
                setTimeout(()=>{ask_whether_harmonize_again_completed(last_mtime);}, hamonize_again_asking_interval);
            }
    }, "application/json", "json");
}

function request_harmonizing_again(){
    document.getElementById("regenerate_hint_panel").hidden = false;
    document.getElementById("audio_waiting_hint").hidden = false;
    document.getElementById("mixed_audio_ctrlr").hidden = true;
    let harmonization_args = collect_args();
    let sent_data = JSON.stringify({"audio_id":audio_id, "args":harmonization_args})
    post_sender("/second/hamonize_again", sent_data, function(xhttp_request){
        ask_whether_harmonize_again_completed(xhttp_request.response.last_mtime);
    }, "application/json", "json");
}

function display_value_of_range(id, suffix=""){
    let nd = document.getElementById(id);
    let val_label = document.getElementById(id+"_val");
    val_label.innerText = nd.value + suffix;
}

function refresh_arg_value_display(){
    let form_node = document.getElementById("harmonization_arg_inputs_form");
    let inputs_list = form_node.getElementsByTagName("input");
    for(let i=0;i<inputs_list.length;i++){
        let input_element = inputs_list[i];
        if(input_element.type != "range") continue;
        setTimeout(()=>{
            input_element.oninput();
        }, 100);
    }
}

function show_arg_panel(){
    document.getElementById("args_panel").hidden = false;
}

function hide_arg_panel(){
    document.getElementById("args_panel").hidden = true;
}

function reset_arg_form(){
    document.getElementById("harmonization_arg_inputs_form").reset();
}

function regenerate_harmony_btn_on_panel_clicked(){
    hide_arg_panel();
    request_harmonizing_again();
}

function collect_args(){
    let arg_octave = parseInt(document.getElementById("arg_octave").value);
    let arg_chord_trend_maj = parseFloat(document.getElementById("arg_chord_trend_maj").value);
    let arg_chord_trend_min = parseFloat(document.getElementById("arg_chord_trend_min").value);
    let arg_chord_trend_dom = parseFloat(document.getElementById("arg_chord_trend_dom").value);
    let arg_chord_trend_domsus4 = parseFloat(document.getElementById("arg_chord_trend_domsus4").value);
    let arg_chord_trend_dim = parseFloat(document.getElementById("arg_chord_trend_dim").value);
    let arg_chord_trend_hdim = parseFloat(document.getElementById("arg_chord_trend_hdim").value);
    let arg_chord_trend_mM = parseFloat(document.getElementById("arg_chord_trend_mM").value);
    let arg_chord_trend_aug_7 = parseFloat(document.getElementById("arg_chord_trend_aug+7").value);
    let arg_chord_trend_aug7 = parseFloat(document.getElementById("arg_chord_trend_aug7").value);
    let arg_selection_range = parseInt(document.getElementById("arg_selection_range").value);
    let arg_antidirection = parseFloat(document.getElementById("arg_antidirection").value);
    let arg_fifth_circle = parseInt(document.getElementById("arg_fifth_circle").value);
    let arg_voicing_openclose = parseInt(document.getElementById("arg_voicing_openclose").value);
    let arg_split_time = parseFloat(document.getElementById("arg_split_time").value);
    let arg_sustain_time = parseFloat(document.getElementById("arg_sustain_time").value);
    let arg_midi_velocity = parseInt(document.getElementById("arg_midi_velocity").value);

    let fifth_award_table = [0, 15, 150, 1500, 15000];
    let args = {
        "octave": arg_octave,
        "chord_type_trend_args": {"maj":arg_chord_trend_maj, "min":arg_chord_trend_min, "dom":arg_chord_trend_dom, 
            "domsus":arg_chord_trend_domsus4, "dim":arg_chord_trend_dim, "hdim":arg_chord_trend_hdim,
            "mM":arg_chord_trend_mM, "aug+7":arg_chord_trend_aug_7, "aug7":arg_chord_trend_aug7},
        "chord_type_selection_range": arg_selection_range,
        "antidirection_award": 1-(arg_antidirection/10),
        "fifth_circle_award": fifth_award_table[arg_fifth_circle],
        "voicing_openclose_stability": arg_voicing_openclose * 25,
        "split_time": parseInt(arg_split_time * 1000),
        "arg_sustain_time": parseInt(arg_sustain_time * 1000),
        "output_midinote_velocity": arg_midi_velocity
    };
    // console.log(args);
    return args;
}

window.onload = get_and_validate_audio_id;
