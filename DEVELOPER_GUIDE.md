Developer Guide
===============


Setup
-----

Follow the [installation](https://docs.facefusion.io/installation), then check out the beta, install the dependencies and start the API:

```
git checkout v4-beta
python facefusion.py api --api-session-limit 32
```

The API options can be passed as arguments or set in the `[api]` section of `facefusion.ini`.

| Option                    | Default     | Choices              |
|---------------------------|-------------|----------------------|
| `--api-host`              | `127.0.0.1` |                      |
| `--api-port`              | `8000`      |                      |
| `--api-session-limit`     | `1`         | `1` to `100`         |
| `--api-security-strategy` | `strict`    | `strict`, `moderate` |


Authentication
--------------

Open a session via `POST /session` with a JSON body, include `api_key` only when `FACEFUSION_API_KEY` is set on the server. Send the `access_token` as `Authorization: Bearer <token>`, WebSockets pass it as first subprotocol `access_token.<token>`.

A session lives 10 minutes and both tokens share that expiry. Refresh via `PUT /session` with the `refresh_token` before it expires, this rotates both tokens and restarts the 10 minutes. Old tokens stop working and an expired session cannot be refreshed.

Only `GET /`, `POST /session`, `PUT /session` and `GET /capabilities` are public. On expiry the session state, assets, streams and sockets are dropped, `DELETE /session` also removes its files.


Flow
----

1. Open a session via `POST /session`
2. Upload the source via `POST /assets?type=source` and the target via `POST /assets?type=target`
3. Select them via `PUT /state?action=select&type=source` and `PUT /state?action=select&type=target`
4. Create a job via `POST /jobs` and add a step via `POST /jobs/{job_id}?action=add`
5. Submit the job via `PATCH /jobs/{job_id}?action=submit`
6. Run the job via `PATCH /jobs/{job_id}?action=run`
7. Poll `GET /jobs/{job_id}` until every step is `completed` or one is `failed`
8. Find the `output` asset named after the job via `GET /assets`
9. Download it via `GET /assets/{asset_id}?action=download`

For real time processing, open a stream via `POST /stream` or use the `/stream` WebSocket for single images instead of creating a job.


Capabilities
------------

`GET /capabilities` returns the supported `formats` and the `arguments`, grouped by section and argument name. Use it to build your options.

| Field     | Description                                                   |
|-----------|---------------------------------------------------------------|
| `default` | initial value, a list when the argument takes multiple values |
| `choices` | allowed values, numeric ranges come fully expanded            |
| `groups`  | sections the argument belongs to                              |

A missing `choices` means free input. The available processors are `age_modifier`, `background_remover`, `deep_swapper`, `expression_restorer`, `face_debugger`, `face_editor`, `face_enhancer`, `face_swapper`, `frame_colorizer`, `frame_enhancer` and `lip_syncer`, each with its own section.


Assets
------

Upload as multipart with one or more parts named `file`. The format is taken from the file extension, uploads are re-encoded and stripped of metadata, `--api-security-strategy moderate` copies audio and video streams instead. Request bodies are capped at 512 MiB.

| Media | Formats                                       |
|-------|-----------------------------------------------|
| audio | flac, m4a, mp3, ogg, opus, wav                |
| image | bmp, jpeg, png, tiff, webp                    |
| video | avi, m4v, mkv, mov, mp4, mpeg, mxf, webm, wmv |

An asset carries `id`, `created_at`, `expires_at`, `type`, `media`, `name`, `format`, `size` and `metadata`. Assets belong to the session, a single job run or retry adds an `output` asset.

| Action     | Parameters                             | Returns                |
|------------|----------------------------------------|------------------------|
| `download` |                                        | the file               |
| `capture`  | `resolution`, `subject`, `frame_index` | a JPEG strip of tiles  |

Capture accepts images and videos. `resolution` is `WxH` between 64 and 4096, `subject=frame` fits each frame, `subject=face` crops every detected face, repeat `frame_index` for videos.


State
-----

`GET /state` returns the options of the session, the same keys as listed by `GET /capabilities`.

| Request                                  | Body                   |
|------------------------------------------|------------------------|
| `PUT /state`                             | option keys and values |
| `PUT /state?action=select&type=source`   | `asset_ids` as list    |
| `PUT /state?action=select&type=target`   | `asset_id` as string   |

Values are checked against the capabilities. Any unknown key or invalid value responds `400` and nothing is applied.


Jobs
----

Jobs belong to the session. A job is `drafted`, `queued`, `completed` or `failed`, steps additionally report `started` while processing. The job status is not part of `GET /jobs/{job_id}`, derive it from the steps or from `GET /jobs?status=`.

The step body takes the options listed by `GET /capabilities`, the minimum is the `processors` list. Source, target and output are taken from the session state. Only one job can be queued at a time, submit and retry respond `409` otherwise. Retry reruns every step of a failed job. Bulk run and retry do not create an `output` asset.


Streaming
---------

Select the `source` and configure the `processors` before streaming, one WebRTC stream per session.

`POST /stream` takes a raw SDP offer as `application/sdp` and responds `201` with the answer. There is no trickle ICE and no STUN or TURN, gather all candidates before sending the offer and make sure the client reaches the server directly. Offer separate send and receive transceivers.

| Media | Codecs                        | Required |
|-------|-------------------------------|----------|
| video | `av1`, `vp9`, `vp8`           | yes      |
| audio | `opus`                        | no       |

The `/stream` WebSocket takes binary images and returns one binary JPEG per decodable image. Frames flagged by the content analyser are blurred.


Misc
----

| Endpoint   | Payload                                          |
|------------|--------------------------------------------------|
| `/metrics` | JSON metrics every 2 seconds                     |
| `/ping`    | ignored, does not extend the session             |

Metrics contain `graphic_devices`, `disks`, `memory`, `network` and `processor`, each value with `value` and `unit`. Closing or expiring the session closes every socket.


Errors
------

| Status | Reason                                                 |
|--------|--------------------------------------------------------|
| 400    | malformed body, invalid parameter or value             |
| 401    | missing, unknown or rotated token, invalid `api_key`   |
| 404    | unknown asset, job or stream                           |
| 409    | job already queued, stream already open                |
| 413    | request body exceeds 512 MiB                           |
| 415    | upload could not be sanitized                          |
| 422    | empty state body                                       |
| 429    | session limit reached                                  |


API
---

### Session

| Method | Endpoint   | Description                                      |
|--------|------------|--------------------------------------------------|
| POST   | `/session` | open a session, returns access and refresh token |
| GET    | `/session` | inspect the current session                      |
| PUT    | `/session` | rotate both tokens and restart the expiry        |
| DELETE | `/session` | close the session and remove its files           |
| WS     | `/ping`    | hold a connection, does not extend the session   |

### State

| Method | Endpoint                     | Description                        |
|--------|------------------------------|------------------------------------|
| GET    | `/state`                     | read the session options           |
| PUT    | `/state`                     | update the session options         |
| PUT    | `/state?action=select&type=` | select `source` or `target` assets |

### Assets

| Method | Endpoint                     | Description                                           |
|--------|------------------------------|-------------------------------------------------------|
| GET    | `/assets`                    | list the assets                                       |
| POST   | `/assets?type=`              | upload `source` or `target` assets                    |
| DELETE | `/assets`                    | delete all assets                                     |
| GET    | `/assets/{asset_id}`         | read an asset                                         |
| GET    | `/assets/{asset_id}?action=` | `download` an asset or `capture` its frames and faces |
| DELETE | `/assets/{asset_id}`         | delete an asset                                       |

### Jobs

| Method | Endpoint                              | Description                                   |
|--------|---------------------------------------|-----------------------------------------------|
| GET    | `/jobs?status=`                       | list the jobs by status                       |
| POST   | `/jobs`                               | create a job                                  |
| PATCH  | `/jobs?action=`                       | `submit`, `run` or `retry` all jobs           |
| DELETE | `/jobs`                               | delete all jobs                               |
| GET    | `/jobs/{job_id}`                      | read a job and its steps                      |
| POST   | `/jobs/{job_id}?action=add`           | add a step                                    |
| PATCH  | `/jobs/{job_id}?action=`              | `submit`, `run` or `retry` a job              |
| DELETE | `/jobs/{job_id}`                      | delete a job                                  |
| POST   | `/jobs/{job_id}/{step_index}?action=` | `add`, `insert` or `remix` a step at an index |
| DELETE | `/jobs/{job_id}/{step_index}`         | remove a step                                 |

### Stream

| Method | Endpoint  | Description                             |
|--------|-----------|-----------------------------------------|
| POST   | `/stream` | send a WebRTC offer, returns the answer |
| DELETE | `/stream` | close the WebRTC stream                 |
| WS     | `/stream` | send images, receive processed images   |

### System

| Method | Endpoint        | Description                        |
|--------|-----------------|------------------------------------|
| GET    | `/`             | read the name and version          |
| GET    | `/capabilities` | discover the options of the engine |
| GET    | `/metrics`      | read the system metrics            |
| WS     | `/metrics`      | receive live metrics               |


CLI
---

Run the command:

```
python facefusion.py [commands] [options]

options:
  -h, --help                                      show this help message and exit
  -v, --version                                   show program's version number and exit

commands:
    run                                           run the program
    batch-run                                     run the program in batch mode
    force-download                                force automate downloads and exit
    benchmark                                     benchmark the program
    api                                           start the API server
    job-list                                      list jobs by status
    job-create                                    create a drafted job
    job-submit                                    submit a drafted job to become a queued job
    job-submit-all                                submit all drafted jobs to become a queued jobs
    job-delete                                    delete a drafted, queued, failed or completed job
    job-delete-all                                delete all drafted, queued, failed and completed jobs
    job-add-step                                  add a step to a drafted job
    job-remix-step                                remix a previous step from a drafted job
    job-insert-step                               insert a step to a drafted job
    job-remove-step                               remove a step from a drafted job
    job-run                                       run a queued job
    job-run-all                                   run all queued jobs
    job-retry                                     retry a failed job
    job-retry-all                                 retry all failed jobs
```
