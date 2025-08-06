# Video Subtitle Generator

Create subtitles in various languages in mere minutes using Whisper and Qwen3-32b via Groq's lightning-fast inference.

## Features
- **Multi-language Support**: 50+ languages with automatic detection
- **Ultra-Fast Processing**: Whisper API powered by Groq for lightning-fast transcription
- **Advanced Translation**: Qwen3-32b by Groq for accurate multilingual translation
- **Video Processing**: Supports MP4, MOV, AVI, MKV, WMV, FLV, WebM, M4V 
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

### Setup & Run

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

That's it! 🎉 The application will be available at `http://localhost:3000`

### Configuration Options

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

## 🙏 Acknowledgments

- [Groq](https://groq.com) for ultra-fast AI inference
- [FFmpeg](https://ffmpeg.org) for video processing
- [FastAPI](https://fastapi.tiangolo.com) & [Next.js](https://nextjs.org) for the frameworks

## 👨‍💻 Author  
Created by **Krish Desai**, AI Applications Engineer Intern at **Groq**.  
Connect with him on [X (formerly Twitter)](https://x.com/thekrishdesai) and [LinkedIn](https://linkedin.com/in/desaikrish).

## 📄 License  
This project is licensed under the **MIT License**.
