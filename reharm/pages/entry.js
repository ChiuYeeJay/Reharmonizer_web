import React from 'react';
import ReactDOM from 'react-dom';

class Entry extends React.Component {

  componentDidMount(){
    console.warn("did");
    document.getElementById("submit_btn").disabled = true;
  }
  on_audio_chosen = () => {
    let submit_btn_element = document.getElementById("submit_btn");
    let fileinput_element = document.getElementById("audio_upload");
    if(fileinput_element.value == "") return;
    // submit_btn_element.disabled = true;
    let url = URL.createObjectURL(fileinput_element.files[0]);
    let audio = new Audio(url);
    audio.oncanplaythrough = ()=>{
        // console.log(audio.duration);
        if(audio.duration > 180){
            alert("audio length too long, it must be less then 180s")
            submit_btn_element.disabled = true;
            // return;
        } else {
          submit_btn_element.disabled = false;
        }
    }
    console.log(submit_btn_element.disabled)
  }
  audio_id = ""
  
  harmonization_suceed = () => {
      if (this.harmonization_request.readyState != XMLHttpRequest.DONE) return;
      if (this.harmonization_request.status === 200) {
          document.getElementById("upload_status").innerText = "redirect..."
          console.warn(this.harmonization_request.responseText)
          window.location.assign(this.harmonization_request.responseText)
      }
      else{
          console.warn("something wrong: " + this.harmonization_request.status);
          window.alert("something wrong: " + this.harmonization_request.status)
      }
  }

  start_harmonization = () => {
      let harmonization_args = {"octave":4}
      this.harmonization_request = new XMLHttpRequest();
      this.harmonization_request.onreadystatechange = this.harmonization_suceed
      this.harmonization_request.open("POST", "/harmonize");
      this.harmonization_request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
      this.harmonization_request.send(JSON.stringify({"args":harmonization_args, "audio_id":this.audio_id}));
  }

  audio2midi_suceeded = () => {
      if (this.audio2midi_request.readyState != XMLHttpRequest.DONE) return;
      if (this.audio2midi_request.status === 200) {
          document.getElementById("upload_status").innerText = "harmonizing..."
          this.start_harmonization()
      }
      else{
          console.warn("something wrong: " + this.audio2midi_request.status);
          window.alert("something wrong: " + this.audio2midi_request.status)
      }
  }

  start_audio2midi = () => {
      this.audio2midi_request = new XMLHttpRequest();
      this.audio2midi_request.onreadystatechange = this.audio2midi_suceeded;
      this.audio2midi_request.open("POST", "/audio2midi");
      this.audio2midi_request.setRequestHeader("Content-Type", "application/json;charset=UTF-8")
      this.audio2midi_request.send(JSON.stringify({"audio_id":this.audio_id}));
  }

  submit_suceeded = () => {
      console.log(this.audio_submit_request.readyState);
      if (this.audio_submit_request.readyState != XMLHttpRequest.DONE) return;
      if (this.audio_submit_request.status === 200) {
          this.audio_id = this.audio_submit_request.response.audio_id;
          console.log("audio_id: " + this.audio_id)
          document.getElementById("upload_status").innerText = "processing audio..."
          this.start_audio2midi()
      }
      else{
          console.warn("something wrong: " + this.audio_submit_request.status);
          window.alert("something wrong: " + this.audio_submit_request.status)
      }
  }

  submit_audio = () => {
      console.log("upload audio")
      let form_element = document.getElementById("audio_form")
      form_element.hidden = true;
      document.getElementById("upload_status").innerText = "uploading audio..."
      
      this.audio_submit_request = new XMLHttpRequest();
      this.audio_submit_request.onreadystatechange = this.submit_suceeded;
      this.audio_submit_request.open("POST", form_element.action);
      this.audio_submit_request.responseType = "json"
      this.audio_submit_request.send(new FormData(form_element));
  }

  render () {
    return (
      <div>
        <title>Reharmonizer</title>
        <h1>Reharmon!zer</h1>
        <div>
          <p>Reharmonizer使你可以上傳任意音檔，系統將會為他量身打造鋼琴的旋律與和聲</p>
          <p>(音檔時長最長為三分鐘，窩們沒有錢去升級伺服器)</p>
        </div>
        <form id="audio_form" method="post" action="/upload" encType="multipart/form-data">
          <label htmlFor="audio_upload">上傳音檔：</label>
          <input name="original_audio" id="audio_upload" type="file" accept="audio/*" formEncType="multipart/form-data" onInput={this.on_audio_chosen} required />
          <input id="submit_btn" type="button" defaultValue="上傳" onClick={this.submit_audio}/>
        </form>
        <p id="upload_status" />
      </div>
    );
  }
}

// window.onload = () => {
//   document.getElementById("submit_btn").disabled = true;
// }

export default Entry
//ReactDOM.render(<Entry />, document.getElementById('root'))