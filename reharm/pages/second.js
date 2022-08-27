import React from 'react';
import ReactDOM from 'react-dom';
import propTypes from 'prop-types';


export default class Result extends React.Component {

    audio_id = ""
    
    get_and_validate_audio_id(){
      console.log("window onload?")
      let url_param = new URLSearchParams(window.location.search);
      if(url_param.has("audio_id")){
          this.audio_id = url_param.get("audio_id");
          console.log("audio_id: " + this.audio_id)
          this.post_sender("/second/validate_audio_id", JSON.stringify({"audio_id":this.audio_id}), this.start, 
                      "application/json", "json");
      }
      else{
          this.go_back_entry();
      }
    } 

    componentDidMount(){
      this.get_and_validate_audio_id();
    }

    // after audio_id being validated, initialze buttons callback and send first requests
    // called by handler of 'get_and_validate_audio_id'
    start = (xhttp_request) => {
        if(!xhttp_request.response.is_valid){
            this.go_back_entry();
        }
        console.warn("start reharmonize");
        document.getElementById("get_mixed_audio_btn").addEventListener("click", this.get_mixed_audio_btn_clicked);
        document.getElementById("back_last_page_btn").addEventListener("click", this.go_back_entry);
        document.getElementById("regenerate_harmony").addEventListener("click", this.request_harmonizing_again);
        this.get_mixed_audio_btn_clicked();
        this.request_midi_dowload_link();
        this.request_chords();
        this.refresh_arg_value_display();
    }

    post_sender = (action, data, handler, content_type="application/json", response_type="") => {
        this.xhttp_request = new XMLHttpRequest();
        this.xhttp_request.onreadystatechange = ()=>{
            if (this.xhttp_request.readyState != XMLHttpRequest.DONE) return;
            if (this.xhttp_request.status !== 200) {
                console.warn("something wrong in " + action + ": " + this.xhttp_request.status);
                window.alert("something wrong: " + this.xhttp_request.status)
                return;
            }

            handler(this.xhttp_request)
        }
        this.xhttp_request.open("POST", action);
        this.xhttp_request.responseType = response_type
        this.xhttp_request.setRequestHeader("Content-Type", content_type+";charset=UTF-8");
        this.xhttp_request.send(data);
    }

    go_back_entry = () => {
        window.location.assign("/")
    }

    mix_audio_response_handler = (xhttp_request) => {
        var binaryData = [];
        binaryData.push(xhttp_request.response);
        let blob_url = window.URL.createObjectURL(new Blob(binaryData))
        document.getElementById("audio_waiting_hint").hidden = true;
        console.warn(blob_url)
        document.getElementById("mixed_audio_ctrlr").src = blob_url;
        document.getElementById("mixed_audio_ctrlr").hidden = false;
        document.getElementById("dl_mixed_audio_link").href = blob_url;
    }

    get_mixed_audio_btn_clicked = () => {
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
            let data = JSON.stringify({"would_be_combined":checked_list, "audio_id":this.audio_id});
            this.post_sender("/second/mix_audio", data, this.mix_audio_response_handler, "application/json", "blob");
        }
    }

    request_midi_dowload_link = () => {
        let melody_data = JSON.stringify({"which_midi":"melody", "audio_id":this.audio_id})
        this.post_sender("/second/get_midi_file", melody_data, function(xhttp_request){
            var binaryData = [];
            binaryData.push(xhttp_request.response);
            let blob_url = window.URL.createObjectURL(new Blob(binaryData))
            document.getElementById("melody_midi_dl_link").href = blob_url;
        }, "application/json", "blob");

        let harmony_data = JSON.stringify({"which_midi":"harmony", "audio_id":this.audio_id})
        this.post_sender("/second/get_midi_file", harmony_data, function(xhttp_request){
            var binaryData = [];
            binaryData.push(xhttp_request.response);
            let blob_url = window.URL.createObjectURL(new Blob(binaryData))
            // let blob_url = URL.createObjectURL(xhttp_request.response)
            document.getElementById("harmony_midi_dl_link").href = blob_url;
        }, "application/json", "blob");
    }

    request_chords = () => {
      this.post_sender("/second/get_chords", JSON.stringify({"audio_id":this.audio_id}), function(xhttp_request){
            document.getElementById("chord_list").innerText = xhttp_request.response;
        }, "application/json", "text");
    }

    request_harmonizing_again = () => {
        document.getElementById("regenerate_hint").hidden = false;
        let harmonization_args = this.collect_args();
        let sent_data = JSON.stringify({"audio_id":this.audio_id, "args":harmonization_args})
        this.post_sender("/second/hamonize_again", sent_data, function(xhttp_request){
            this.get_mixed_audio_btn_clicked();
            this.request_midi_dowload_link();
            this.request_chords();
            document.getElementById("regenerate_hint").hidden = true;
        }, "application/json", "text")
    }

    display_value_of_range = (id, suffix="") => {
        let nd = document.getElementById(id);
        let val_label = document.getElementById(id+"_val");
        val_label.innerText = nd.value + suffix;
    }

    refresh_arg_value_display = () => {
        let form_node = document.getElementById("harmonization_arg_inputs_form");
        let inputs_list = form_node.getElementsByTagName("input");
        for(let i=0;i<inputs_list.length;i++){
            let input_element = inputs_list[i]
            if(input_element.type != "range") continue;
            setTimeout(()=>{
                //input_element.onInput();
                input_element.dispatchEvent(new Event("onInput"));
            }, 100);
        }
    }

    show_hide_arg_form = () => {
        let switch_btn = document.getElementById("harmonization_arg_inputs_switch"); 
        let form_node = document.getElementById("harmonization_arg_inputs_form");
        if(form_node.hidden){
            form_node.hidden = false;
            switch_btn.innerText = "隱藏調整參數";
        }
        else{
            form_node.hidden = true;
            switch_btn.innerText = "顯示調整參數";
        }
    }

    collect_args = () => {
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
    render () {
      return (
        <div>
          <title>Reharmonizer</title>
          <h1>Reharmon!zer</h1>
          <p>音檔已經處理完成，你可以預覽、下載這邊的東東，或是選擇重新配和聲</p>
          <div>
            <p>音檔預覽：</p>
            <input type="checkbox" id="original_audio_checkbox" defaultChecked />
            <label htmlFor="original_audio">原音檔</label>
            <input type="checkbox" id="melody_audio_checkbox" defaultChecked />
            <label htmlFor="melody">旋律</label>
            <input type="checkbox" id="harmony_audio_checkbox" defaultChecked />
            <label htmlFor="harmony">和聲</label>
            <input type="button" id="get_mixed_audio_btn" defaultValue="生成" />
            <br />
            <audio id="mixed_audio_ctrlr" controls />
            <p id="audio_waiting_hint" hidden>waiting audio...</p>
            <a id="dl_mixed_audio_link" href download="mixed_audio.wav">
              <button id="dl_mixed_audio_btn">下載音檔</button>
            </a>
          </div>
          <div>
            <a id="melody_midi_dl_link" download="melody.mid">
              <button id="melody_midi_dlbtn">下載旋律midi</button>
            </a>
            <a id="harmony_midi_dl_link" download="harmony.mid">
              <button id="harmony_midi_dlbtn">下載和聲midi</button>
            </a>
          </div>
          <div>
            <p>和弦表</p>
            <div id="chord_list_div" style={{height: '200px', width: '200px', overflowY: 'scroll'}}>
              <p id="chord_list" />
            </div>
          </div>
          <div>
            <button id="harmonization_arg_inputs_switch" onClick="show_hide_arg_form();">顯示調整參數</button>
            <button id="regenerate_harmony">重新生成和聲</button>
            <p id="regenerate_hint" hidden>重新生成中...</p>
            <form id="harmonization_arg_inputs_form" onreset="refresh_arg_value_display()" hidden>
              <label htmlFor="arg_octave">八度：</label>
              <input type="range" id="arg_octave" name="arg_octave" onInput="display_value_of_range('arg_octave')" min={1} max={7} step={1} defaultValue={4} />
              <label htmlFor="arg_octave" id="arg_octave_val">4</label>
              <fieldset>
                <legend>和弦出現傾向</legend>
                <label htmlFor="arg_chord_trend_maj">大和弦：</label>
                <input type="range" id="arg_chord_trend_maj" name="arg_chord_trend_maj" onInput="display_value_of_range('arg_chord_trend_maj')" min={0} max={2} step="0.01" defaultValue="1.5" />
                <label htmlFor="arg_chord_trend_maj" id="arg_chord_trend_maj_val">1.5</label>
                <br />
                <label htmlFor="arg_chord_trend_min">小和弦：</label>
                <input type="range" id="arg_chord_trend_min" name="arg_chord_trend_min" onInput="display_value_of_range('arg_chord_trend_min')" min={0} max={2} step="0.01" defaultValue="1.25" />
                <label htmlFor="arg_chord_trend_min" id="arg_chord_trend_min_val">1.25</label>
                <br />
                <label htmlFor="arg_chord_trend_dom">屬七和弦：</label>
                <input type="range" id="arg_chord_trend_dom" name="arg_chord_trend_dom" onInput="display_value_of_range('arg_chord_trend_dom')" min={0} max={2} step="0.01" defaultValue={1} />
                <label htmlFor="arg_chord_trend_dom" id="arg_chord_trend_dom_val">1</label>
                <br />
                <label htmlFor="arg_chord_trend_domsus4">屬七sus4和弦：</label>
                <input type="range" id="arg_chord_trend_domsus4" name="arg_chord_trend_domsus4" onInput="display_value_of_range('arg_chord_trend_domsus4')" min={0} max={2} step="0.01" defaultValue={1} />
                <label htmlFor="arg_chord_trend_domsus4" id="arg_chord_trend_domsus4_val">1</label>
                <br />
                <label htmlFor="arg_chord_trend_dim">減七和弦：</label>
                <input type="range" id="arg_chord_trend_dim" name="arg_chord_trend_dim" onInput="display_value_of_range('arg_chord_trend_dim')" min={0} max={2} step="0.01" defaultValue="0.75" />
                <label htmlFor="arg_chord_trend_dim" id="arg_chord_trend_dim_val">0.75</label>
                <br />
                <label htmlFor="arg_chord_trend_hdim">半減七和弦：</label>
                <input type="range" id="arg_chord_trend_hdim" name="arg_chord_trend_hdim" onInput="display_value_of_range('arg_chord_trend_hdim')" min={0} max={2} step="0.01" defaultValue="0.75" />
                <label htmlFor="arg_chord_trend_hdim" id="arg_chord_trend_hdim_val">0.75</label>
                <br />
                <label htmlFor="arg_chord_trend_mM">小大七和弦：</label>
                <input type="range" id="arg_chord_trend_mM" name="arg_chord_trend_mM" onInput="display_value_of_range('arg_chord_trend_mM')" min={0} max={2} step="0.01" defaultValue="0.75" />
                <label htmlFor="arg_chord_trend_mM" id="arg_chord_trend_mM_val">0.75</label>
                <br />
                <label htmlFor="arg_chord_trend_aug+7">增和弦+7：</label>
                <input type="range" id="arg_chord_trend_aug+7" name="arg_chord_trend_aug+7" onInput="display_value_of_range('arg_chord_trend_aug+7')" min={0} max={2} step="0.01" defaultValue="0.75" />
                <label htmlFor="arg_chord_trend_aug+7" id="arg_chord_trend_aug+7_val">0.75</label>
                <br />
                <label htmlFor="arg_chord_trend_aug7">增七和弦：</label>
                <input type="range" id="arg_chord_trend_aug7" name="arg_chord_trend_aug7" onInput="display_value_of_range('arg_chord_trend_aug7')" min={0} max={2} step="0.01" defaultValue="0.75" />
                <label htmlFor="arg_chord_trend_aug7" id="arg_chord_trend_aug7_val">0.75</label>
              </fieldset>
              <label htmlFor="arg_selection_range">隨機程度：</label>
              <input type="range" id="arg_selection_range" name="arg_selection_range" onInput="display_value_of_range('arg_selection_range')" min={1} max={20} step={1} defaultValue={5} />
              <label htmlFor="arg_selection_range" id="arg_selection_range_val">5</label>
              <br />
              <label htmlFor="arg_antidirection">外聲部反向的傾向：</label>
              <input type="range" id="arg_antidirection" name="arg_antidirection" onInput="display_value_of_range('arg_antidirection')" min={0} max={5} step="0.1" defaultValue={2} />
              <label htmlFor="arg_antidirection" id="arg_antidirection_val">2</label>
              <br />
              <label htmlFor="arg_fifth_circle">五度連接的傾向：</label>
              <input type="range" id="arg_fifth_circle" name="arg_fifth_circle" onInput="display_value_of_range('arg_fifth_circle')" min={0} max={4} step={1} defaultValue={2} />
              <label htmlFor="arg_fifth_circle" id="arg_fifth_circle_val">2</label>
              <br />
              <label htmlFor="arg_voicing_openclose">voicing的開閉穩定程度：</label>
              <input type="range" id="arg_voicing_openclose" name="arg_voicing_openclose" onInput="display_value_of_range('arg_voicing_openclose')" min={0} max={4} step={1} defaultValue={2} />
              <label htmlFor="arg_voicing_openclose" id="arg_voicing_openclose_val">2</label>
              <br />
              <label htmlFor="arg_split_time">空白多久換和弦：</label>
              <input type="range" id="arg_split_time" name="arg_split_time" onInput="display_value_of_range('arg_split_time', 's')" min={0} max={1} step="0.01" defaultValue="0.2" />
              <label htmlFor="arg_split_time" id="arg_split_time_val">2s</label>
              <br />
              <label htmlFor="arg_sustain_time">持續多久換和弦：</label>
              <input type="range" id="arg_sustain_time" name="arg_sustain_time" onInput="display_value_of_range('arg_sustain_time', 's')" min={0} max={10} step="0.01" defaultValue="2.4" />
              <label htmlFor="arg_sustain_time" id="arg_sustain_time_val">2s</label>
              <br />
              <label htmlFor="arg_midi_velocity">和聲部分的midi note velocity：</label>
              <input type="range" id="arg_midi_velocity" name="arg_midi_velocity" onInput="display_value_of_range('arg_midi_velocity')" min={1} max={127} step={1} defaultValue={100} />
              <label htmlFor="arg_midi_velocity" id="arg_midi_velocity_val">100</label>
              <br />
              <input type="reset" />
            </form>
          </div>
          <div>
            <button id="back_last_page_btn">回到上一頁</button>
          </div>
        </div>
      );
    }
}
