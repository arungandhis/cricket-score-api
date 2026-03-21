# 🏏 Cricket Live Studio

A web app that simulates a cricket match from a **Cricsheet JSON** file (e.g., IPL 2008 match data). It provides:

- Live scoreboard & ball‑by‑ball commentary
- Audio commentary (text‑to‑speech)
- Video commentary (recordable canvas overlay) that can be downloaded and uploaded to YouTube

## 🚀 Live Demo
After deploying on Render, open the site, upload your JSON, and start the simulation.

## 📂 How to Use
1. Upload a valid Cricsheet JSON file (like `335982.json`).
2. Press **START** to begin ball‑by‑ball simulation.
3. Adjust speed, pause, or step manually.
4. Click **Start Recording** to capture the video overlay, then **Stop & Save** and download the video.
5. Upload the downloaded `.webm` file to YouTube.

## 🛠️ Deployment on Render
1. Push this repository to GitHub.
2. On [Render.com](https://render.com), create a new **Static Site**.
3. Connect your GitHub repo.
4. Set **Build Command** to empty (no build needed).
5. Set **Publish Directory** to the root (where `index.html` is located).
6. Click **Create Static Site**. Your app will be live in minutes.

## 📄 License
MIT