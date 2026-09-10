# SceneVault hosted studio

This is a new, independent web application. It does not call the placeholder analysis functions in the original CLI.

## Deployment

Native Python service. Build command: `bash hosted/build.sh`. Start command: `uvicorn hosted.server:app --host 0.0.0.0 --port $PORT --workers 1`. Health endpoint: `/health`. Set `HF_HUB_OFFLINE=1` for runtime after the build has cached all three models; omit it during the initial build or use the start command `HF_HUB_OFFLINE=1 uvicorn hosted.server:app --host 0.0.0.0 --port $PORT --workers 1`.

Required secret: `STUDIO_PASSWORD`. The application refuses login if it is missing. Do not commit the password. The server uses private session cookies; all uploads, job records and downloads require a session. Uploads are chunked to avoid large single-request limits.

Use `STUDIO_DATA` for the job directory and point it at persistent disk for survival across redeploys. The default is ephemeral `/tmp/scenevault-data`. CPU models are cached during build. Only one job runs at a time. Interrupted jobs are marked on restart. Uploaded media and rendered results stay until the owner deletes the project. No automatic deletion or cloud backup is claimed.

## Actual processing

Whisper produces word-timed narration and source dialogue; CLIP compares sampled frames with the narration; MiniLM compares nearby source speech with narration meaning. Each shot retains five alternatives, raw similarity scores and a manual approval flag. No similarity score is presented as calibrated accuracy. Short events between two-second samples can be missed. Face detection chooses a gentle pan center; it does not identify the person. Uploaded images can be chosen by visual relevance. No web image search or fabricated scene generation is used.

The renderer preserves source proportions, applies a real rounded panel mask over a blurred backdrop, optional gentle pan/zoom, short fade-ins, subtle grading, highlighted captions, animated quote labels and quiet synthesized whooshes. 4K output is 2160 × 3840; it does not restore detail absent from the source. Alpha masks shape the panel; person segmentation and object tracking are not implemented.

An uploaded exact script corrects the recognized wording while preserving speech intervals (replacement words share their recognized interval). A substantially different script is rejected. Without a script, captions use raw speech recognition and may misspell names. Candidate edits and approvals can be saved and rendered again. Always inspect the final draft for narrative context and caption names.

## Verification

Run `python -m unittest discover -s hosted/tests`. Full model and media smoke tests are separate and use actual video/audio inputs. The Render bill and final plan must be approved before a paid instance is created.

Verified on 2026-09-10: private API/session checks, upload ordering and invalid media rejection, origin/path checks, non-overlapping caption timings; real CLIP + MiniLM + Whisper scene matching on a 50-second source excerpt and 10-second narration; 2160 × 3840 H.264/AAC output matching the 10-second narration. The 4K render peaked at approximately 1.3 GiB on this test machine. This is a small smoke test, not a guarantee of narrative accuracy or a full-length production benchmark.

Deployment proposal: one Render 1 CPU / 2 GB native Python web service at the published $25/month compute rate (before taxes, bandwidth or optional disk). Serial processing and separate matching/rendering processes limit peak memory. No paid resource has been provisioned. A persistent disk is optional and must be configured separately; without it project files may disappear on deploy/restart. A GitHub branch alone is not a deployed website.
