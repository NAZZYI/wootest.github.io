<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Video Clipper</title>

<style>
body{
    background:#1b1b1b;
    color:white;
    font-family:Arial;
    margin:0;
    padding:20px;
}

.container{
    max-width:900px;
    margin:auto;
}

h1{
    text-align:center;
}

video{
    width:100%;
    margin-top:20px;
    border-radius:10px;
    background:black;
}

input[type=file]{
    width:100%;
    padding:10px;
    margin-top:15px;
}

.slider{
    width:100%;
}

.box{
    background:#2c2c2c;
    padding:20px;
    border-radius:10px;
    margin-top:20px;
}

.time{
    font-size:18px;
    margin-bottom:10px;
}

button{
    width:100%;
    padding:15px;
    font-size:18px;
    background:#ff0000;
    color:white;
    border:none;
    border-radius:10px;
    cursor:pointer;
}

button:hover{
    background:#cc0000;
}

#message{
    margin-top:20px;
    text-align:center;
    font-size:18px;
}
</style>

</head>
<body>

<div class="container">

<h1>🎬 Video Clipper</h1>

<input type="file" id="videoFile" accept="video/*">

<video id="video" controls></video>

<div class="box">

<div class="time">
Start:
<span id="startLabel">00:00:00</span>
</div>

<input
type="range"
id="startSlider"
class="slider"
value="0"
min="0"
max="0">

<br><br>

<div class="time">
End:
<span id="endLabel">00:00:00</span>
</div>

<input
type="range"
id="endSlider"
class="slider"
value="0"
min="0"
max="0">

<br><br>

<button id="clipButton">
Create Clip
</button>

<div id="message"></div>

</div>

</div>

<script>

const video=document.getElementById("video");
const file=document.getElementById("videoFile");

const start=document.getElementById("startSlider");
const end=document.getElementById("endSlider");

const startLabel=document.getElementById("startLabel");
const endLabel=document.getElementById("endLabel");

function format(seconds){

seconds=Math.floor(seconds);

const h=Math.floor(seconds/3600);
const m=Math.floor((seconds%3600)/60);
const s=seconds%60;

return String(h).padStart(2,"0")+":"+
String(m).padStart(2,"0")+":"+
String(s).padStart(2,"0");

}

file.onchange=function(){

const selected=this.files[0];

if(!selected) return;

video.src=URL.createObjectURL(selected);

video.onloadedmetadata=function(){

start.max=Math.floor(video.duration);
end.max=Math.floor(video.duration);

start.value=0;
end.value=Math.floor(video.duration);

startLabel.innerHTML=format(0);
endLabel.innerHTML=format(video.duration);

}

};

start.oninput=function(){

startLabel.innerHTML=format(this.value);

if(Number(this.value)>Number(end.value)){

end.value=this.value;
endLabel.innerHTML=format(this.value);

}

};

end.oninput=function(){

endLabel.innerHTML=format(this.value);

if(Number(end.value)<Number(start.value)){

start.value=end.value;
startLabel.innerHTML=format(end.value);

}

};

document.getElementById("clipButton").onclick=function(){

const clipLength=end.value-start.value;

document.getElementById("message").innerHTML=

"<b>Clip Ready</b><br><br>"+
"Start: "+format(start.value)+"<br>"+
"End: "+format(end.value)+"<br>"+
"Length: "+format(clipLength)+"<br><br>"+
"This demo selects the clip. A backend service is needed to actually create a new video file.";

};

</script>

</body>
</html>
