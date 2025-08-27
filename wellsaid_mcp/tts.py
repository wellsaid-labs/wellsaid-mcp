from dataclasses import dataclass
from pathlib import Path
from wellsaid_mcp.mcp_server import mcp
import secrets
import os
from mcp.types import TextContent, AudioContent, Annotations
import logging
from wellsaid_mcp.utils import client
import httpx
import base64
from pydantic import BaseModel#, Field, ConfigDict
from typing import Any, Generator, Iterator, Literal, TypedDict, Dict
import time
from mcp.server.fastmcp import Context
from enum import Enum
import concurrent
import asyncio
from concurrent.futures import Future


class ClipContent(TextContent):
    type:Literal["text"]="text"
    clip_id:str
    file_path:Path


class ClipParams(TypedDict):
    text:str
    speaker_id:str
    model:str

class TaskStatus(Enum):
    STARTED = "started"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    SUCCESS = "success"
class TtsTask(BaseModel):
    job_id:str
    status:TaskStatus
    message:str
    # future:Future

# -------------------------------------------------------------------
# Background task registry
# -------------------------------------------------------------------
_task_registry: Dict[str, TtsTask] = {}
_executor = concurrent.futures.ThreadPoolExecutor()


@mcp.tool(description="Check the status of a background TTS generation task by job ID."
)
def get_tts_status(job_id: str) -> TtsTask:
    task = _task_registry.get(job_id)
    if not task:
        return TtsTask(job_id=job_id, status=TaskStatus.ERROR, message="Task not found")
    return task


# ----


def make_output_path(output_directory: str | None) -> Path:
    path = Path(output_directory).expanduser() if output_directory else Path.home() / "Desktop"
    path.mkdir(parents=True, exist_ok=True)
    return path

def make_output_file(text: str, output_path: Path, extension: str = "mp3") -> Path:
    safe_text = "".join(c for c in text[:20] if c.isalnum() or c in (" ", "-")).rstrip()
    filename = f"tts_{safe_text.replace(' ', '_')}_{os.getpid()}-{secrets.token_hex(3)}.{extension}"
    return output_path / filename

@mcp.tool(
    description="""Convert text to speech using WellSaid API and save the audio file.
    This is most appropriate when wanting to store a file for longer term use.
    
    ⚠️ COST WARNING: This tool makes a paid API call to WellSaid Labs.

    Args:
        text: Text to convert
        speaker_id: ID of the WellSaid speaker to use
        filename: Filename to use for the generated file. Do not include the extension, it will be added automatically
        model: Voice model to use (legacy or caruso)
        output_directory: (Optional) Directory to save the output audio file

    
    The returned ClipContent value has a clip_id that can be used in other methods like combine_clips
    """
)
async def text_to_speech(
    context: Context,
    text: str,
    speaker_id: int,
    filename:str,
    model: str = "caruso",
    output_directory: str | None = None,
) -> ClipContent|TextContent:
    logging.info("Doing tts")
    if not text:
        return TextContent(type="text", text="Error: Text is required.")
    
    # Step 1: Make TTS request
    response = client.post("/clips", json={
        "text": text,
        "speaker_id": speaker_id,
        "model": model
    }, timeout=30)

    if response.status_code != 200:
        return TextContent(type="text", text=f"Error from WellSaid API: {response.text}")

    clip = response.json()
    clip_id = clip["clip_id"]

    await context.info("Clip submitted")
    # Step 2: Poll for clip readiness (basic sync style)
    clip_ready = False
    for _ in range(20):  # Wait ~10 seconds max
        check = client.get(f"/clips/{clip_id}")
        if check.status_code != 200:
            break
        status = check.json()["status"]
        if status == "COMPLETE":
            clip_ready = True
            await context.info("Clip completed")
            break
        if status == "PROCESSING":
            await context.info("Clip is processing...")
            pass
        time.sleep(3)

    if not clip_ready:
        return TextContent(type="text", text="Clip did not complete in time.")

    # Step 3: Download audio
    clip_data = check.json()
    audio_url = clip_data.get("url")
    if not audio_url:
        return TextContent(type="text", text="No audio URL found.")

    audio_response = httpx.get(audio_url)
    output_path = make_output_path(output_directory)
    output_file = make_output_file(filename, output_path)
    with open(output_file, "wb") as f:
        f.write(audio_response.content)

    return ClipContent(
        clip_id=clip_id,
        file_path=output_file,
        text=f"✅ Success! Audio saved to {output_file}"

    )



# @mcp.tool(
#     description="""Convert text to speech using WellSaid API and returns the audio content.
#     This is streaming based and does not save files anywhere. Particularly useful for 
#     creating different samples and trying things out.
    
#     ⚠️ COST WARNING: This tool makes a paid API call to WellSaid Labs.

#     Args:
#         text: Text to convert
#         speaker_id: ID of the WellSaid speaker to use
#         model: Voice model to use (legacy or caruso)
#     """
# )
def text_to_speech_stream(
    text: str,
    speaker_id: int,
    model: str = "legacy",
    output_directory: str | None = None,
) -> TextContent|AudioContent:
    logging.info("Doing tts")
    if not text:
        return TextContent(type="text", text="Error: Text is required.")
    
    # Step 1: Make TTS request
    response = client.post("/stream", json={
        "text": text,
        "speaker_id": speaker_id,
        "model": model
    })

    if response.status_code != 200:
        return TextContent(type="text", text=f"Error from WellSaid API: {response.text}")

    
    logging.info("Sent in a stream request")
    # Check for audio MIME type
    if not response.headers.get("Content-Type", "").startswith("audio/"):
        raise ValueError("Expected an audio response, got: " + response.headers.get("Content-Type", ""))
    mimeType = response.headers.get("Content-Type", "")
    # Convert to base64-encoded string
    audio_base64 = base64.b64encode(response.content).decode("utf-8")

    audio_content = AudioContent(data=audio_base64,mimeType=mimeType, type='audio')

    return audio_content


@mcp.tool(description="""
    Creates multiple clips and combines them into a single output. Useful when the text is longer
          than the allowed limit for a single clip, or when wanting to create a clip with multiple voices.
          
    Args:
        clip_values: Clips to combine, in order. A clip id is found in the clip_id property of ClipContent responses. It
          is not the filename from the locally saved clip.
        filename: Filename to use for the saved file. Don't include a file extension, the appropriate one will be added automatically.
        gaps: list of floats for gaps to include between the clips. Value is in seconds. Optional, if not included, 
          will default to no gap. Can be of length 1, where that same silence is applied to gap between all clips,
          or of length n-1, where n is the length of the list of clip_ids.
        output_directory: (Optional) Directory to save the output audio file
          
    Returns a TaskStatus object with a job_id. This can be used to query the get_tts_status function and check the status of the job.
          It is recommended to only check once every 10 seconds.
""")
async def create_multiple_clips_and_combine(
    context: Context,
    clip_values:list[ClipParams], 
    filename:str,
    gaps:list[float]=None,
    output_directory: str | None = None,
    ) -> TaskStatus:
    job_id = secrets.token_hex(8)
    output_path = Path(output_directory or ".").expanduser() / f"{filename}-{secrets.token_hex(3)}.txt"

    task = TtsTask(job_id=job_id, status=TaskStatus.STARTED, message="Task started")
    _task_registry[job_id] = task

    loop = asyncio.get_running_loop()
    # Run in executor
    # future = loop.run_in_executor(_executor,create_multiple_clips_and_combine_in_background, task, context, clip_values, gaps, output_directory)
    asyncio.create_task(create_multiple_clips_and_combine_in_background( task, context, clip_values,filename, gaps, output_directory))
    # task = future
    

    return task



async def create_multiple_clips_and_combine_in_background(
    task:TtsTask,
    context: Context,
    clip_values:list[ClipParams],
    filename:str, 
    gaps:list[float]=None,
    output_directory: str | None = None,
    ): #-> Iterator[TextContent]:
    task.status = TaskStatus.PROCESSING
    # Step 1: Make TTS request
    logging.info("submitting clips request")
    await context.info("submitting clips request")
    create_clips_response = client.post("/clips", json=clip_values, timeout=60)

    if create_clips_response.status_code != 200:
        logging.info(create_clips_response)
        task.status = TaskStatus.ERROR
        task.message = f"Failed to create clips : {create_clips_response.content}"
        # return TextContent(type="text", text=f"Failed to create clips : {create_clips_response.content}")
    
    clip_ids = create_clips_response.json()["clip_ids"]
    logging.info(f"Waiting on {len(clip_ids)} clips to finish processing")
    await context.info("Submitted clips for processing")
    # yield TextContent(type="text", text="Clips submitted, waiting on processing")
    total_clips = len(clip_ids)
    completed_clips = 0
    for clip_id in clip_ids:
        clip_ready = False
        logging.info(f"checking on clip {clip_id}")
        for _ in range(20):  # Wait ~10 seconds max
            check = client.get(f"/clips/{clip_id}")
            if check.status_code != 200:
                break
            status = check.json()["status"]
            if status == "COMPLETE":
                clip_ready = True
                break
            time.sleep(3)
        if clip_ready:
            completed_clips += 1
            await context.report_progress(completed_clips, total_clips, f"Completed {completed_clips}/{total_clips}")
            await context.info(f"Completed {completed_clips}/{total_clips}")
            # yield TextContent(type="text", text=f"Completed {completed_clips}/{total_clips}")
        if not clip_ready:
            task.status = TaskStatus.ERROR
            task.message = "Clips did not finish processing in time"
            # return TextContent("Clips did not finish processing in time")

    # yield TextContent(type="text", text="Clips created, combining and saving result...")
    combine_response = client.post("/clips/combine", json={
        "clip_ids": clip_ids,
        "pause_durations":gaps
    })

    mimeType = combine_response.headers.get("Content-Type", "")

    if mimeType != "audio/mpeg":
        logging.error(f"Bad result type on combining clips")
        logging.error(f"{combine_response.content}")
        # return TextContent(type="text", text=f"Error combining clips")
        task.status = TaskStatus.ERROR
        task.message = f"Bad result type on combining clips"

    
    output_path = make_output_path(output_directory)
    output_file = make_output_file(f"{filename}-{secrets.token_hex(3)}", output_path)
    with open(output_file, "wb") as f:
        f.write(combine_response.content)
    
    # return TextContent(type="text", text=f"Saved file to {output_file}")
    task.status = TaskStatus.SUCCESS
    task.message = f"Saved file to {output_file}"
