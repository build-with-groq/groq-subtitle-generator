# Video Subtitle Generator
The Groq Subtitle Generator (Project SubLingo) is a demo that showcases Groq in action through high-speed transcription and translation, allowing users to generate burned-in subtitles across languages in just seconds. Users can upload a video in any of the 50+ supported languages, choose the same or a different language for subtitles, review the transcription, and watch the magic unfold. Once a video is uploaded, FFmpeg converts it to a WAV audio file, which is then passed to the Video Processing Service. This audio is transcribed using OpenAI’s Whisper Large V3-turbo model, powered by Groq. Users can edit individual segments to ensure accuracy. If translation is selected, the content is then translated using the Qwen3-32B model through the Groq API. The final subtitles are formatted as an SRT file and rendered onto the video using FFmpeg to produce the final output. Here is a [sample video](https://github.com/user-attachments/assets/1d81f956-c0e7-4995-83ac-856aec1b8b58) file to test the demo out!

https://github.com/user-attachments/assets/97c79dc0-75a9-4ae9-8925-9cf06b7d2dfa

## Features
- **Multi-language Support**: 50+ languages with automatic detection
- **Ultra-Fast Processing**: Whisper API powered by Groq for lightning-fast transcription
- **Advanced Translation**: Qwen3-32b by Groq for accurate multilingual translation
- **Video Processing**: Supports MP4, MOV, AVI
- **Burned-in Subtitles**: Create videos with permanently embedded subtitles
- **Edit Before Translation**: Review and edit transcription for perfect accuracy

## 🛠️ Tech Stack

### Backend
- **FastAPI**
- **Groq API**
- **FFmpeg**
- **Pydantic**

### Frontend
- **Next.js 15**
- **TypeScript**
- **Tailwind CSS**
- **Lucide React**

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- FFmpeg installed
- Groq API key (get free access at [groq.com](https://groq.com))

### Install FFmpeg

**macOS**:
```bash
brew install ffmpeg
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows**:
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

## 🎯 Setup & Run

Choose your preferred setup method:

### Option 1: Automated Setup (Recommended)

**Easy one-command setup:**

1. **Clone and setup everything**:
   ```bash
   git clone <repository-url>
   cd groq-subtitle-generator
   chmod +x setup.sh start.sh
   ./setup.sh
   ```

2. **Add your Groq API key**:
   ```bash
   # Edit backend/.env and add your API key
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Start the application**:
   ```bash
   ./start.sh
   ```

The scripts handle all dependency installation, virtual environment setup, and server management automatically!

### Option 2: Manual Setup

**For those who prefer manual control:**

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd groq-subtitle-generator
   ```

2. **Setup Python environment**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cd ..
   ```

3. **Setup Node.js dependencies**:
   ```bash
   npm install
   ```

4. **Create environment file**:
   ```bash
   # Create backend/.env file
   cat > backend/.env << 'EOF'
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=qwen/qwen3-32b
   GROQ_WHISPER_MODEL=whisper-large-v3
   EOF
   ```

5. **Start backend server**:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```

6. **In a new terminal, start frontend**:
   ```bash
   npm run dev
   ```

That's it! 🎉 The application will be available at `http://localhost:3000`

## ⚙️ Configuration Options

The `backend/.env` file supports these settings:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Model Selection (optional)
GROQ_MODEL=qwen/qwen3-32b
GROQ_WHISPER_MODEL=whisper-large-v3  # Options: whisper-large-v3, whisper-large-v3-turbo, distil-whisper-large-v3-en
```

## 🎬 Usage Workflow

1. **📤 Upload Video**: Drag and drop or select a video file
2. **🌐 Configure Languages**: 
   - Source language
   - Target language for subtitles
3. **🎵 Transcription**: Whisper transcribes the audio with timestamps
4. **✏️ Edit & Review**: Review and edit transcription for perfect accuracy
   - Edit individual segments with timestamps
   - Ensure quality before translation
5. **🔄 Translation**: Qwen3-32b translates to your target language
6. **🎬 Generation**: Create subtitled video with burned-in subtitles
7. **📥 Download**: Get your subtitled video


## 🔍 Troubleshooting

**Scripts not executable?**
```bash
chmod +x setup.sh start.sh
```

**FFmpeg not found?**
Make sure FFmpeg is installed and available in your PATH.

**API key issues?**
Ensure your Groq API key is correctly set in `backend/.env`.

**Port conflicts?**
The app uses ports 3000 (frontend) and 8000 (backend). Make sure these are available.

## 🙏 Sample Video To Experiment (Credit: MovieClips.Com, CastleRock Entertaiment)

https://github.com/user-attachments/assets/80b8d55c-8b30-4149-865c-9239cb916145

## 🙏 Acknowledgments

- [Groq](https://groq.com) for ultra-fast AI inference
- [FFmpeg](https://ffmpeg.org) for video processing
- [FastAPI](https://fastapi.tiangolo.com) & [Next.js](https://nextjs.org) for the frameworks

## 👨‍💻 Author  
Created by **Krish Desai**, AI Applications Engineer Intern at **Groq**.  
Connect with him on [X (formerly Twitter)](https://x.com/thekrishdesai) and [LinkedIn](https://linkedin.com/in/desaikrish).

## 📄 License  
This project is licensed under the **MIT License**.
