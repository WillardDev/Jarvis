# Jarvis Wire Protocol

Binary and text frames travel over one WebSocket.

## Up (browser -> backend)
- **Binary:** Raw PCM16 mono, 16 kHz sample rate. Audio chunks sent while `record_start` is held.
- **Text (JSON):**
  - `{"type":"record_start"}` — begin capturing / signal user speaking
  - `{"type":"record_stop"}` — end of user turn (Phase 1 push-to-talk)
  - `{"type":"interrupt"}` — barge-in; stop playback immediately
  - `{"type":"ping"}` — keepalive (optional)

## Down (backend -> browser)
- **Binary:** Raw PCM16 mono, 24 kHz sample rate. TTS audio as it is synthesized.
- **Text (JSON):**
  - `{"type":"ready","input_sample_rate":16000,"output_sample_rate":24000}`
  - `{"type":"state","state":"idle"|"listening"|"thinking"|"speaking"}`
  - `{"type":"user_transcript","text":"...","final":false|true}`
  - `{"type":"assistant_transcript","text":"...","final":false|true}`
  - `{"type":"latency","turn":1,"marks":{"speech_end":12.3,...}}` — stage boundaries in ms since turn start
  - `{"type":"interrupted"}` — playback was stopped due to barge-in
  - `{"type":"error","message":"..."}`

## Latency marks
- `speech_end` — server learned the user stopped speaking
- `stt_final` — final transcript received
- `llm_first_token` — first token from the model
- `tts_first_audio` — first TTS audio frame produced
- `audio_first_sent` — first audio byte written to the WebSocket
- `llm_done` / `tts_done` — response complete

The browser measures "first audio played" locally and adds it to the debug panel.
