const express = require('express');
const axios = require('axios');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { Readable } = require('stream');

// Google TTS (will be null if credentials not provided)
let textToSpeech = null;
try {
  textToSpeech = require('@google-cloud/text-to-speech');
} catch (e) {
  console.warn('Google TTS library not installed, skipping');
}

const app = express();
app.use(cors());
app.use(express.json());

// --------------------------------------------------------------
// Configuration
// --------------------------------------------------------------
const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY;
const ELEVENLABS_VOICE_ID = '21m00Tcm4TlvDq8ikWAM'; // Rachel

console.log('API Key starts with:', process.env.ELEVENLABS_API_KEY ? process.env.ELEVENLABS_API_KEY.substring(0,10) : 'NOT SET');


const CACHE_DIR = path.join(__dirname, 'cache');
if (!fs.existsSync(CACHE_DIR)) fs.mkdirSync(CACHE_DIR, { recursive: true });

// --------------------------------------------------------------
// Providers list (will be populated based on credentials)
// --------------------------------------------------------------
let providers = [];

// --------------------------------------------------------------
// ElevenLabs provider
// --------------------------------------------------------------
async function elevenLabsGenerate(text, style) {
  let stability = 0.5, similarity = 0.75, styleBoost = 0.5;
  if (style === 'excited') {
    stability = 0.4; similarity = 0.8; styleBoost = 0.9;
  } else if (style === 'dramatic') {
    stability = 0.3; similarity = 0.85; styleBoost = 1.0;
  }
  const response = await axios({
    method: 'POST',
    url: `https://api.elevenlabs.io/v1/text-to-speech/${ELEVENLABS_VOICE_ID}`,
    headers: {
      'Accept': 'audio/mpeg',
      'xi-api-key': ELEVENLABS_API_KEY,
      'Content-Type': 'application/json'
    },
    data: {
      text: text,
      voice_settings: { stability, similarity_boost: similarity, style: styleBoost, use_speaker_boost: true }
    },
    responseType: 'stream'
  });
  return response.data;
}

if (ELEVENLABS_API_KEY) {
  providers.push({
    name: 'ElevenLabs',
    remaining: 10000, // free tier characters
    unit: 'characters',
    priority: 1,
    generate: elevenLabsGenerate
  });
}

// --------------------------------------------------------------
// Google Cloud TTS provider (using the library)
// --------------------------------------------------------------
let googleClient = null;
if (textToSpeech && (process.env.GOOGLE_APPLICATION_CREDENTIALS || process.env.GOOGLE_API_KEY)) {
  try {
    googleClient = new textToSpeech.TextToSpeechClient();
  } catch (e) {
    console.warn('Google TTS client init failed', e.message);
  }
}

async function googleTtsGenerate(text, style) {
  if (!googleClient) throw new Error('Google TTS not configured');
  let speakingRate = 0.95;
  let pitch = 0.0;
  if (style === 'excited') {
    speakingRate = 1.05;
    pitch = 2.0;
  } else if (style === 'dramatic') {
    speakingRate = 1.1;
    pitch = 1.5;
  }
  const request = {
    input: { text: text },
    voice: { languageCode: 'en-GB', name: 'en-GB-Wavenet-A' },
    audioConfig: { audioEncoding: 'MP3', speakingRate, pitch }
  };
  const [response] = await googleClient.synthesizeSpeech(request);
  const buffer = Buffer.from(response.audioContent, 'base64');
  const stream = new Readable();
  stream.push(buffer);
  stream.push(null);
  return stream;
}

if (googleClient) {
  providers.push({
    name: 'GoogleCloud',
    remaining: 1000000, // first 1M chars free
    unit: 'characters',
    priority: 2,
    generate: googleTtsGenerate
  });
}

// Sort by priority
providers.sort((a, b) => a.priority - b.priority);

// --------------------------------------------------------------
// Cache helper
// --------------------------------------------------------------
function getCacheKey(text, style) {
  let stability = 0.5, similarity = 0.75, styleBoost = 0.5;
  if (style === 'excited') {
    stability = 0.4; similarity = 0.8; styleBoost = 0.9;
  } else if (style === 'dramatic') {
    stability = 0.3; similarity = 0.85; styleBoost = 1.0;
  }
  const data = `${text}|${stability}|${similarity}|${styleBoost}`;
  return crypto.createHash('md5').update(data).digest('hex') + '.mp3';
}

// --------------------------------------------------------------
// Main endpoint
// --------------------------------------------------------------
app.post('/speak', async (req, res) => {
  const { text, style = 'normal' } = req.body;
  if (!text) return res.status(400).send('Missing text');

  // Check cache
  const cacheKey = getCacheKey(text, style);
  const cachePath = path.join(CACHE_DIR, cacheKey);
  if (fs.existsSync(cachePath)) {
    res.set('Content-Type', 'audio/mpeg');
    return fs.createReadStream(cachePath).pipe(res);
  }

  // Try providers
  for (let provider of providers) {
    const textLength = text.length;
    if (provider.unit === 'characters' && provider.remaining < textLength) {
      console.log(`${provider.name} insufficient characters (${provider.remaining} left, need ${textLength})`);
      continue;
    }

    try {
      console.log(`Using ${provider.name} for: "${text.substring(0, 50)}..."`);
      const audioStream = await provider.generate(text, style);

      // Save to cache
      const writeStream = fs.createWriteStream(cachePath);
      await new Promise((resolve, reject) => {
        audioStream.pipe(writeStream);
        writeStream.on('finish', resolve);
        writeStream.on('error', reject);
        audioStream.on('error', reject);
      });

      // Deduct usage
      if (provider.unit === 'characters') {
        provider.remaining -= textLength;
      } else if (provider.unit === 'requests') {
        provider.remaining -= 1;
      }
      console.log(`${provider.name} remaining ${provider.remaining} ${provider.unit}`);

      // Serve
      res.set('Content-Type', 'audio/mpeg');
      return fs.createReadStream(cachePath).pipe(res);
    } catch (err) {
      console.error(`${provider.name} error:`, err.message);
      // Continue to next provider
    }
  }

  res.status(503).send('All TTS providers unavailable or quota exceeded');
});

// --------------------------------------------------------------
// Health check
// --------------------------------------------------------------
app.get('/health', (req, res) => res.send('OK'));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`TTS server running on port ${PORT}`));