const express = require('express');
const axios = require('axios');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const app = express();
app.use(cors());
app.use(express.json());

const CACHE_DIR = path.join(__dirname, 'cache');
if (!fs.existsSync(CACHE_DIR)) fs.mkdirSync(CACHE_DIR, { recursive: true });

// Helper: generate cache key from text, voice, and API key (hash of key)
function getCacheKey(text, voiceId, apiKey) {
  const keyHash = crypto.createHash('md5').update(apiKey || 'default').digest('hex').substring(0, 8);
  const textHash = crypto.createHash('md5').update(text).digest('hex');
  return `${keyHash}_${voiceId}_${textHash}.mp3`;
}

// ElevenLabs request (uses provided key and voice)
async function elevenLabsGenerate(text, style, apiKey, voiceId) {
  let stability = 0.5, similarity = 0.75, styleBoost = 0.5;
  if (style === 'excited') {
    stability = 0.4; similarity = 0.8; styleBoost = 0.9;
  } else if (style === 'dramatic') {
    stability = 0.3; similarity = 0.85; styleBoost = 1.0;
  }
  const response = await axios({
    method: 'POST',
    url: `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
    headers: {
      'Accept': 'audio/mpeg',
      'xi-api-key': apiKey,
      'Content-Type': 'application/json'
    },
    data: {
      text: text,
      voice_settings: {
        stability,
        similarity_boost: similarity,
        style: styleBoost,
        use_speaker_boost: true
      }
    },
    responseType: 'stream'
  });
  return response.data;
}

// Endpoint to fetch available voices (needs API key)
app.post('/voices', async (req, res) => {
  const { apiKey } = req.body;
  if (!apiKey) return res.status(400).send('Missing API key');
  try {
    const response = await axios.get('https://api.elevenlabs.io/v1/voices', {
      headers: { 'xi-api-key': apiKey }
    });
    res.json(response.data.voices);
  } catch (err) {
    console.error('Error fetching voices:', err.message);
    if (err.response) {
      console.error('Status:', err.response.status);
      console.error('Data:', err.response.data);
    }
    res.status(500).send('Could not fetch voices');
  }
});

// Main TTS endpoint
app.post('/speak', async (req, res) => {
  const { text, style = 'normal', apiKey, voiceId } = req.body;
  if (!text) return res.status(400).send('Missing text');
  if (!apiKey) return res.status(400).send('Missing ElevenLabs API key');
  if (!voiceId) return res.status(400).send('Missing voice ID');

  // Log API key (masked) for debugging
  const maskedKey = apiKey.substring(0, 8) + '...' + apiKey.slice(-4);
  console.log(`Received request for text: "${text.substring(0, 50)}..."`);
  console.log(`API key: ${maskedKey}, voiceId: ${voiceId}, style: ${style}`);

  // Check cache
  const cacheKey = getCacheKey(text, voiceId, apiKey);
  const cachePath = path.join(CACHE_DIR, cacheKey);
  if (fs.existsSync(cachePath)) {
    console.log('Serving from cache:', cacheKey);
    res.set('Content-Type', 'audio/mpeg');
    return fs.createReadStream(cachePath).pipe(res);
  }

  try {
    console.log('Calling ElevenLabs API...');
    const audioStream = await elevenLabsGenerate(text, style, apiKey, voiceId);
    const writeStream = fs.createWriteStream(cachePath);
    await new Promise((resolve, reject) => {
      audioStream.pipe(writeStream);
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
      audioStream.on('error', reject);
    });
    console.log('Audio generated and cached.');
    res.set('Content-Type', 'audio/mpeg');
    fs.createReadStream(cachePath).pipe(res);
  } catch (err) {
    console.error('ElevenLabs error:', err.message);
    if (err.response) {
      console.error('Status:', err.response.status);
      // Read the response body for more details (it might be a string or stream)
      if (err.response.data && typeof err.response.data.pipe === 'function') {
        // If it's a stream, read it into a buffer
        const chunks = [];
        err.response.data.on('data', chunk => chunks.push(chunk));
        err.response.data.on('end', () => {
          const body = Buffer.concat(chunks).toString();
          console.error('Response body:', body);
        });
      } else {
        console.error('Response data:', err.response.data);
      }
    }
    res.status(500).send('TTS error');
  }
});

app.get('/health', (req, res) => res.send('OK'));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`TTS server running on port ${PORT}`));