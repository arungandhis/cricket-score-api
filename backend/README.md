# Cricket TTS Backend

This server provides text-to-speech using multiple providers (ElevenLabs, Google Cloud) with caching and usage tracking.

## Setup

1. Install dependencies: `npm install`
2. Set environment variables:
   - `ELEVENLABS_API_KEY` (required for ElevenLabs)
   - `GOOGLE_APPLICATION_CREDENTIALS` (path to service account JSON) for Google Cloud
3. Run: `npm start`

## API Endpoint

- `POST /speak` – expects JSON `{ text, style }` (style: normal, excited, dramatic). Returns MP3 audio.
- `GET /health` – returns OK.

Cached audio is stored in the `cache/` directory.