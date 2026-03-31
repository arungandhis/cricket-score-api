const express = require('express');
const axios = require('axios');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { Readable } = require('stream');

const app = express();
app.use(cors());
app.use(express.json());

const CACHE_DIR = path.join(__dirname, 'cache');
if (!fs.existsSync(CACHE_DIR)) fs.mkdirSync(CACHE_DIR, { recursive: true });

// Rate limiting: queue for processing requests
let requestQueue = [];
let processing = false;
const MIN_INTERVAL_MS = 2000; // 2 seconds between requests (adjust as needed)

function processQueue() {
  if (processing) return;
  if (requestQueue.length === 0) return;
  processing = true;
  const { req, res } = requestQueue.shift();
  handleRequest(req, res).finally(() => {
    processing = false;
    setTimeout(() => processQueue(), MIN_INTERVAL_MS);
  });
}

// Helper: generate cache key that includes provider, text, voice, and key hash
function getCacheKey(provider, text, voiceId, apiKey) {
  const keyHash = crypto.createHash('md5').update(apiKey || 'default').digest('hex').substring(0, 8);
  const textHash = crypto.createHash('md5').update(text).digest('hex');
  return `${provider}_${keyHash}_${voiceId}_${textHash}.mp3`;
}

// ---------- ElevenLabs ----------
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

// ---------- Google Cloud TTS ----------
async function googleTtsGenerate(text, style, apiKey, voiceId) {
  let speakingRate = 0.95;
  let pitch = 0.0;
  if (style === 'excited') {
    speakingRate = 1.05;
    pitch = 2.0;
  } else if (style === 'dramatic') {
    speakingRate = 1.1;
    pitch = 1.5;
  }
  const url = `https://texttospeech.googleapis.com/v1/text:synthesize?key=${apiKey}`;
  const payload = {
    input: { text: text },
    voice: { languageCode: 'en-GB', name: voiceId || 'en-GB-Wavenet-A' },
    audioConfig: {
      audioEncoding: 'MP3',
      speakingRate: speakingRate,
      pitch: pitch
    }
  };
  const response = await axios.post(url, payload);
  const audioContent = response.data.audioContent;
  const buffer = Buffer.from(audioContent, 'base64');
  const stream = new Readable();
  stream.push(buffer);
  stream.push(null);
  return stream;
}

// ---------- Azure TTS ----------
async function azureTtsGenerate(text, style, apiKey, region, voiceId) {
  let rate = 0;
  let pitch = 0;
  if (style === 'excited') {
    rate = 15; // +15% speed
    pitch = 2; // +2 semitones
  } else if (style === 'dramatic') {
    rate = -5; // slower for dramatic effect
    pitch = -1;
  }
  
  const ssml = `
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
      <voice name="${voiceId}">
        <prosody rate="${rate}%" pitch="${pitch}st">
          ${text}
        </prosody>
      </voice>
    </speak>
  `;
  
  const url = `https://${region}.tts.speech.microsoft.com/cognitiveservices/v1`;
  
  const response = await axios({
    method: 'POST',
    url: url,
    headers: {
      'Ocp-Apim-Subscription-Key': apiKey,
      'Content-Type': 'application/ssml+xml',
      'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
      'User-Agent': 'CricketBroadcastPro'
    },
    data: ssml,
    responseType: 'stream'
  });
  
  return response.data;
}

// ---------- New endpoint: fetch recent matches ZIP ----------
app.get('/api/recent-matches', async (req, res) => {
  try {
    const zipUrl = 'https://cricsheet.org/downloads/recently_added_7_male_json.zip';
    console.log('Fetching recent matches ZIP from:', zipUrl);
    const response = await axios({
      method: 'get',
      url: zipUrl,
      responseType: 'stream'
    });
    res.setHeader('Content-Type', 'application/zip');
    res.setHeader('Access-Control-Allow-Origin', '*');
    response.data.pipe(res);
  } catch (error) {
    console.error('Error fetching recent matches:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
    }
    res.status(500).json({ error: 'Failed to fetch recent matches' });
  }
});

// ---------- Voice List Endpoints (with Azure) ----------
app.post('/voices', async (req, res) => {
  const { provider, apiKey, region } = req.body;
  if (!provider || !apiKey) return res.status(400).send('Missing provider or API key');
  
  try {
    if (provider === 'elevenlabs') {
      const response = await axios.get('https://api.elevenlabs.io/v1/voices', {
        headers: { 'xi-api-key': apiKey }
      });
      res.json(response.data.voices);
    } 
    else if (provider === 'google') {
      const url = `https://texttospeech.googleapis.com/v1/voices?key=${apiKey}`;
      const response = await axios.get(url);
      const englishVoices = response.data.voices.filter(v => 
        v.languageCodes && v.languageCodes.some(lc => lc.startsWith('en'))
      );
      res.json(englishVoices);
    }
    else if (provider === 'azure') {
      if (!region) return res.status(400).send('Missing Azure region');
      const url = `https://${region}.tts.speech.microsoft.com/cognitiveservices/voices/list`;
      const response = await axios({
        method: 'GET',
        url: url,
        headers: {
          'Ocp-Apim-Subscription-Key': apiKey
        }
      });
      // Filter English voices and format for frontend
      const englishVoices = response.data.filter(voice => 
        voice.Locale && voice.Locale.startsWith('en-')
      );
      res.json(englishVoices);
    }
    else {
      res.status(400).send('Invalid provider');
    }
  } catch (err) {
    console.error(`Error fetching voices for ${provider}:`, err.message);
    if (err.response) {
      console.error('Status:', err.response.status);
      if (err.response.data && typeof err.response.data === 'object') {
        console.error('Response data:', JSON.stringify(err.response.data).substring(0, 500));
      }
    }
    res.status(500).send('Could not fetch voices');
  }
});

// ---------- Main TTS Endpoint (with Azure support and fallback) ----------
async function handleRequest(req, res) {
  const {
    text,
    style = 'normal',
    provider,
    apiKey,
    voiceId,
    region,
    fallbackProvider,
    fallbackApiKey,
    fallbackVoiceId,
    fallbackRegion
  } = req.body;

  if (!text) return res.status(400).send('Missing text');
  if (!provider || !apiKey || !voiceId) {
    return res.status(400).send('Missing provider, API key, or voice ID');
  }

  console.log(`Processing request for provider: ${provider}, text: "${text.substring(0, 50)}..."`);

  // Primary cache key (include region for Azure)
  const cacheKey = getCacheKey(provider + (region || ''), text, voiceId, apiKey);
  const cachePath = path.join(CACHE_DIR, cacheKey);
  if (fs.existsSync(cachePath)) {
    console.log('Serving from cache:', cacheKey);
    res.set('Content-Type', 'audio/mpeg');
    return fs.createReadStream(cachePath).pipe(res);
  }

  // Try primary provider
  let errorMsg = '';

  try {
    let audioStream;
    if (provider === 'elevenlabs') {
      audioStream = await elevenLabsGenerate(text, style, apiKey, voiceId);
    } else if (provider === 'google') {
      audioStream = await googleTtsGenerate(text, style, apiKey, voiceId);
    } else if (provider === 'azure') {
      if (!region) throw new Error('Azure region is required');
      audioStream = await azureTtsGenerate(text, style, apiKey, region, voiceId);
    } else {
      throw new Error('Invalid provider');
    }
    
    // Save to cache
    const writeStream = fs.createWriteStream(cachePath);
    await new Promise((resolve, reject) => {
      audioStream.pipe(writeStream);
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
      audioStream.on('error', reject);
    });
    console.log('Audio generated and cached (primary).');
    res.set('Content-Type', 'audio/mpeg');
    return fs.createReadStream(cachePath).pipe(res);
  } catch (err) {
    console.error(`Primary provider ${provider} failed:`, err.message);
    if (err.response) {
      console.error('Status:', err.response.status);
      if (err.response.data && typeof err.response.data.pipe === 'function') {
        const chunks = [];
        err.response.data.on('data', chunk => chunks.push(chunk));
        err.response.data.on('end', () => {
          const body = Buffer.concat(chunks).toString();
          console.error('Response body:', body);
        });
      } else if (err.response.data) {
        console.error('Response data:', JSON.stringify(err.response.data).substring(0, 500));
      }
    }
    errorMsg = err.message;

    // Try fallback if provided
    if (fallbackProvider && fallbackApiKey && fallbackVoiceId) {
      console.log(`Attempting fallback to ${fallbackProvider}...`);
      try {
        let fallbackStream;
        if (fallbackProvider === 'elevenlabs') {
          fallbackStream = await elevenLabsGenerate(text, style, fallbackApiKey, fallbackVoiceId);
        } else if (fallbackProvider === 'google') {
          fallbackStream = await googleTtsGenerate(text, style, fallbackApiKey, fallbackVoiceId);
        } else if (fallbackProvider === 'azure') {
          if (!fallbackRegion) throw new Error('Azure fallback region is required');
          fallbackStream = await azureTtsGenerate(text, style, fallbackApiKey, fallbackRegion, fallbackVoiceId);
        } else {
          throw new Error('Invalid fallback provider');
        }
        
        // Save fallback to its own cache
        const fallbackCacheKey = getCacheKey(fallbackProvider + (fallbackRegion || ''), text, fallbackVoiceId, fallbackApiKey);
        const fallbackCachePath = path.join(CACHE_DIR, fallbackCacheKey);
        const writeStream = fs.createWriteStream(fallbackCachePath);
        await new Promise((resolve, reject) => {
          fallbackStream.pipe(writeStream);
          writeStream.on('finish', resolve);
          writeStream.on('error', reject);
          fallbackStream.on('error', reject);
        });
        console.log('Fallback succeeded, audio cached.');
        res.set('Content-Type', 'audio/mpeg');
        return fs.createReadStream(fallbackCachePath).pipe(res);
      } catch (fallbackErr) {
        console.error(`Fallback provider ${fallbackProvider} also failed:`, fallbackErr.message);
        if (fallbackErr.response) console.error('Fallback response:', fallbackErr.response.status);
        errorMsg += `; fallback: ${fallbackErr.message}`;
      }
    }
    // If we get here, all attempts failed
    res.status(500).send(`TTS error: ${errorMsg}`);
  }
}

// Endpoint to accept requests (adds to queue)
app.post('/speak', (req, res) => {
  requestQueue.push({ req, res });
  processQueue();
});

app.get('/health', (req, res) => res.send('OK'));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`TTS server running on port ${PORT}`));