import { FFmpeg } from "https://unpkg.com/@ffmpeg/ffmpeg@0.12.10/dist/esm/index.js";
import { fetchFile } from "https://unpkg.com/@ffmpeg/util@0.12.1/dist/esm/index.js";


const ffmpeg = new FFmpeg();

const videoFile = document.getElementById("videoFile");
const video = document.getElementById("video");
const clipButton = document.getElementById("clipButton");

const clipNumber = document.getElementById("clipNumber");
const message = document.getElementById("message");
const clips = document.getElementById("clips");


let selectedVideo = null;


// Load video preview
videoFile.addEventListener("change", () => {

    selectedVideo = videoFile.files[0];

    if (!selectedVideo) return;

    video.src = URL.createObjectURL(selectedVideo);

    message.innerHTML = "Video loaded.";

});


// Create clips
clipButton.addEventListener("click", async () => {


    if (!selectedVideo) {

        alert("Please upload a video first.");
        return;

    }


    clips.innerHTML = "";


    message.innerHTML = "Loading video engine...";


    if (!ffmpeg.loaded) {

        await ffmpeg.load();

    }


    message.innerHTML = "Preparing video...";


    await ffmpeg.writeFile(
        "input.mp4",
        await fetchFile(selectedVideo)
    );


    const totalDuration = video.duration;

    const amount = Number(clipNumber.value);

    const clipTime = totalDuration / amount;


    message.innerHTML = "Creating clips...";


    for (let i = 0; i < amount; i++) {


        const start = Math.floor(i * clipTime);

        const filename = `clip_${i + 1}.mp4`;


        await ffmpeg.exec([

            "-i",
            "input.mp4",

            "-ss",
            String(start),

            "-t",
            String(Math.floor(clipTime)),

            "-c",
            "copy",

            filename

        ]);



        const fileData = await ffmpeg.readFile(filename);


        const blob = new Blob(

            [fileData.buffer],

            { type: "video/mp4" }

        );


        const url = URL.createObjectURL(blob);



        clips.innerHTML += `

        <div>

            <h3>Clip ${i + 1}</h3>

            <video controls>

                <source src="${url}" type="video/mp4">

            </video>


            <br>

            <a href="${url}" download="${filename}">
                Download Clip ${i + 1}
            </a>

        </div>

        `;


        message.innerHTML =
        `Finished clip ${i + 1} of ${amount}`;

    }


    message.innerHTML = "✅ All clips finished!";


});
