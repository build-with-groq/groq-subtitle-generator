'use client'
import React, { useState, useCallback, useRef, memo } from 'react'
import { Upload, Play, Download, Globe, Clock, FileText, CheckCircle, AlertCircle, Eye } from 'lucide-react'

//types for managing the status and file info
interface JobStatus {
  job_id: string
  status: string
  progress: number
  message: string
  output_path?: string
  subtitle_path?: string
}

interface FileInfo {
  filename: string
  size: number
  duration?: number
  format?: string
  resolution?: string
  fps?: number
}

interface FileInfoCardProps {
  icon: React.ComponentType<{ className?: string }>
  iconColor: string
  label: string
  value: string
  title?: string
}

interface FileInfoSectionProps {
  fileInfo: FileInfo
  title: string
  icon: React.ComponentType<{ className?: string }>
  gradientFrom: string
  gradientTo: string
  borderColor: string
  iconColor: string
  formatFileSize: (bytes: number) => string
  formatDuration: (seconds: number) => string
  getFileExtension: (filename: string) => string
  getAspectRatio: (resolution: string) => string
  getEstimatedBitrate: (size: number, duration: number) => string
}


//list of supported languages by qwen3-32b. if you change the model, please update this list.
const SUPPORTED_LANGUAGES = {
  'en': 'English',
  'es': 'Spanish',
  'fr': 'French',
  'de': 'German',
  'it': 'Italian',
  'pt': 'Portuguese',
  'ru': 'Russian',
  'ja': 'Japanese',
  'ko': 'Korean',
  'zh': 'Chinese',
  'ar': 'Arabic',
  'hi': 'Hindi',
  'th': 'Thai',
  'vi': 'Vietnamese',
  'nl': 'Dutch',
  'sv': 'Swedish',
  'da': 'Danish',
  'fi': 'Finnish',
  'pl': 'Polish',
  'tr': 'Turkish',
  'cs': 'Czech',
  'hu': 'Hungarian',
  'ro': 'Romanian',
  'bg': 'Bulgarian',
  'hr': 'Croatian',
  'sk': 'Slovak',
  'sl': 'Slovenian',
  'et': 'Estonian',
  'lv': 'Latvian',
  'lt': 'Lithuanian',
  'uk': 'Ukrainian',
  'he': 'Hebrew',
  'fa': 'Persian',
  'ur': 'Urdu',
  'bn': 'Bengali',
  'ta': 'Tamil',
  'te': 'Telugu',
  'ml': 'Malayalam',
  'kn': 'Kannada',
  'gu': 'Gujarati',
  'mr': 'Marathi',
  'ne': 'Nepali',
  'si': 'Sinhala',
  'my': 'Burmese',
  'km': 'Khmer',
  'lo': 'Lao',
  'ka': 'Georgian',
  'sw': 'Swahili',
  'af': 'Afrikaans',
  'ms': 'Malay',
  'id': 'Indonesian'
}

//info card component
const FileInfoCard = memo<FileInfoCardProps>(({ icon: Icon, iconColor, label, value, title }) => (
  <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
    <div className="text-center">
      <div className={`w-8 h-8 bg-${iconColor}-100 rounded-full flex items-center justify-center mx-auto mb-2`}>
        <Icon className={`w-4 h-4 text-${iconColor}-600`} />
      </div>
      <span className="text-gray-500 block text-sm mb-1">{label}</span>
      <span 
        className="text-gray-900 font-medium text-sm block truncate max-w-full px-1" 
        title={title || value}
      >
        {value}
      </span>
    </div>
  </div>
))

FileInfoCard.displayName = 'FileInfoCard'

//file info section component to display video info
const FileInfoSection = memo<FileInfoSectionProps>(({
  fileInfo,
  title,
  icon: TitleIcon,
  gradientFrom,
  gradientTo,
  borderColor,
  iconColor,
  formatFileSize,
  formatDuration,
  getFileExtension,
  getAspectRatio,
  getEstimatedBitrate
}) => {
  const fileInfoCards = [
    {
      icon: FileText,
      iconColor: 'blue',
      label: 'Filename',
      value: fileInfo.filename,
      title: fileInfo.filename
    },
    {
      icon: Play,
      iconColor: 'purple',
      label: 'File Type',
      value: getFileExtension(fileInfo.filename)
    },
    {
      icon: Globe,
      iconColor: 'green',
      label: 'Size',
      value: formatFileSize(fileInfo.size)
    },
    ...(fileInfo.duration ? [{
      icon: Clock,
      iconColor: 'orange',
      label: 'Duration',
      value: formatDuration(fileInfo.duration)
    }] : []),
    ...(fileInfo.resolution ? [{
      icon: Eye,
      iconColor: 'indigo',
      label: 'Resolution',
      value: fileInfo.resolution
    }, {
      icon: Eye,
      iconColor: 'pink',
      label: 'Aspect Ratio',
      value: getAspectRatio(fileInfo.resolution)
    }] : []),
    ...(fileInfo.fps ? [{
      icon: Play,
      iconColor: 'yellow',
      label: 'Frame Rate',
      value: `${fileInfo.fps.toFixed(1)} FPS`
    }] : []),
    ...(fileInfo.duration ? [{
      icon: Upload,
      iconColor: 'red',
      label: 'Est. Bitrate',
      value: getEstimatedBitrate(fileInfo.size, fileInfo.duration)
    }] : []),
    ...(fileInfo.format ? [{
      icon: FileText,
      iconColor: 'teal',
      label: 'Format',
      value: fileInfo.format
    }] : [])
  ]

  return (
    <div className={`bg-gradient-to-r from-${gradientFrom} to-${gradientTo} rounded-xl p-6 border border-${borderColor}`}>
      <h3 className="font-semibold text-gray-900 mb-6 text-lg flex items-center">
        <TitleIcon className={`w-5 h-5 mr-2 text-${iconColor}-600`} />
        {title}
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {fileInfoCards.map((card, index) => (
          <FileInfoCard key={index} {...card} />
        ))}
      </div>
    </div>
  )
})

FileInfoSection.displayName = 'FileInfoSection'

//main component with all the state and logic for video subtitle generation
export default function VideoSubtitleGenerator() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [targetLanguage, setTargetLanguage] = useState<string>('en')
  const [sourceLanguage, setSourceLanguage] = useState<string>('')
  const [jobId, setJobId] = useState<string>('')
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [fileInfo, setFileInfo] = useState<FileInfo | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string>('')
  const [dragActive, setDragActive] = useState(false)
  const [showVideoPreview, setShowVideoPreview] = useState(false)
  const [transcription, setTranscription] = useState<any>(null)
  const [isEditingTranscription, setIsEditingTranscription] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }, [])

  const formatDuration = useCallback((seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }, [])

  const getAspectRatio = useCallback((resolution: string): string => {
    if (!resolution) return 'Unknown'
    const [width, height] = resolution.split('x').map(Number)
    if (!width || !height) return 'Unknown'
    
    const gcd = (a: number, b: number): number => b === 0 ? a : gcd(b, a % b)
    const divisor = gcd(width, height)
    return `${width / divisor}:${height / divisor}`
  }, [])

  const getEstimatedBitrate = useCallback((size: number, duration: number): string => {
    if (!duration || duration === 0) return 'Unknown'
    const bitrate = (size * 8) / duration / 1000 // convert to kbps
    if (bitrate > 1000) {
      return `${(bitrate / 1000).toFixed(1)} Mbps`
    }
    return `${bitrate.toFixed(0)} kbps`
  }, [])

  const getFileExtension = useCallback((filename: string): string => {
    return filename.split('.').pop()?.toUpperCase() || 'Unknown'
  }, [])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      const file = files[0]
      if (file.type.startsWith('video/')) {
        setSelectedFile(file)
      } else {
        setError('Please select a video file')
      }
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setError('')
    }
  }, [])

  const uploadVideo = useCallback(async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()
      setJobId(data.job_id)
      setFileInfo({
        filename: data.filename,
        size: data.size
      })
            
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }, [selectedFile])

  const startProcessing = useCallback(async (jobId: string) => {
    setIsProcessing(true)
    
    try {
      const formData = new FormData()
      formData.append('target_language', targetLanguage)
      if (sourceLanguage) {
        formData.append('source_language', sourceLanguage)
      }

      const response = await fetch(`http://localhost:8000/process/${jobId}`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to start processing')
      }

      pollStatus(jobId)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Processing failed')
      setIsProcessing(false)
    }
  }, [targetLanguage, sourceLanguage])

  const pollStatus = useCallback(async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`http://localhost:8000/status/${jobId}`)
        if (response.ok) {
          const status = await response.json()
          setJobStatus(status)
          
          if (status.status === 'completed') {
            setIsProcessing(false)
          } else if (status.status === 'failed') {
            setError(status.message)
            setIsProcessing(false)
          } else if (status.status === 'transcription_complete') {
            // transcription is ready for review
            setIsProcessing(false)
            await fetchTranscription(jobId)
          } else {
            setTimeout(poll, 1000)
          }
        }
      } catch (err) {
        console.error('Polling error:', err)
        setTimeout(poll, 2000)
      }
    }
    
    poll()
  }, [])

  const fetchTranscription = useCallback(async (jobId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/transcription/${jobId}`)
      if (response.ok) {
        const data = await response.json()
        setTranscription(data.transcription)
        setIsEditingTranscription(true)
      }
    } catch (err) {
      setError('Failed to fetch transcription')
    }
  }, [])

  const continueWithTranscription = useCallback(async (editedTranscription: any) => {
    try {
      setIsEditingTranscription(false)
      setIsProcessing(true)
      
      const response = await fetch(`http://localhost:8000/transcription/${jobId}/continue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editedTranscription)
      })

      if (response.ok) {
        pollStatus(jobId)
      } else {
        setError('Failed to continue processing')
        setIsProcessing(false)
      }
    } catch (err) {
      setError('Failed to continue processing')
      setIsProcessing(false)
    }
  }, [jobId, pollStatus])

  const updateTranscriptionSegment = useCallback((index: number, newText: string) => {
    if (transcription && transcription.segments) {
      const updatedSegments = [...transcription.segments]
      updatedSegments[index].text = newText
      
      const updatedText = updatedSegments.map(seg => seg.text).join(' ')
      
      setTranscription({
        ...transcription,
        segments: updatedSegments,
        text: updatedText
      })
    }
  }, [transcription])

  const downloadVideo = useCallback(async () => {
    if (!jobId) return
    
    try {
      const response = await fetch(`http://localhost:8000/download/${jobId}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `subtitled_video_${jobId}.mp4`
        a.click()
        window.URL.revokeObjectURL(url)
      }
    } catch (err) {
      setError('Download failed')
    }
  }, [jobId])

  const resetForm = useCallback(() => {
    setSelectedFile(null)
    setJobId('')
    setJobStatus(null)
    setFileInfo(null)
    setIsUploading(false)
    setIsProcessing(false)
    setError('')
    setShowVideoPreview(false)
    setTranscription(null)
    setIsEditingTranscription(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <div className="flex justify-center mb-8">
          <img 
                src="/groq-labs-logo.png" 
                alt="GroqLabs Logo" 
                className="h-15 w-auto"
              />
          </div>
        </div>
        </div>

      <div className="max-w-7xl mx-auto px-6">
        {/* title section */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">Auto Multilingual Subtitle Generator</h1>
          <p className="text-xl text-gray-600 mb-2 py-2">
          Lightning-fast AI-powered multilingual subtitles.
          </p>
          <p className="text-xl text-gray-600 mb-2 py-2">
          Powered by <span className="font-semibold">Groq.</span>
          </p>
          </div>

        {/* main area */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
            {!jobId ? (
              /* upload section */
              <div className="space-y-8">
                {/* file upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">Select Video File</label>
                  <div
                    className={`border-2 border-dashed rounded-lg p-12 text-center transition-all duration-300 ${
                      dragActive
                        ? "border-orange-500 bg-orange-50"
                        : "border-gray-300 hover:border-orange-400 hover:bg-gray-50"
                    }`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="video/*"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    {selectedFile ? (
                      <div className="space-y-4">
                        <div className="flex items-center justify-center space-x-3">
                          <FileText className="w-12 h-12 text-orange-500" />
                          <div className="text-left min-w-0 flex-1">
                            <span className="text-xl font-medium text-gray-900 block truncate max-w-xs" title={selectedFile.name}>
                              {selectedFile.name}
                            </span>
                            <p className="text-gray-500">{formatFileSize(selectedFile.size)}</p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <Upload className="w-16 h-16 text-gray-400 mx-auto" />
                        <div>
                          <p className="text-xl font-medium text-gray-900 mb-2">
                            Drop your video file here or click to browse
                          </p>
                          <p className="text-gray-500">Supports MP4, MOV or AVI up to 25MB</p>
                          <p className="text-gray-500 text-sm mt-1">Keep videos under 5-10 minutes for optimal performance</p>
                        </div>
                      </div>
                    )}
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="mt-6 px-8 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium border border-gray-300"
                    >
                      Choose File
                    </button>
                  </div>
                </div>

                {/* language selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">Source Language</label>
                    <select
                      value={sourceLanguage}
                      onChange={(e) => setSourceLanguage(e.target.value)}
                      className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    >
                      <option value="">Auto-detect</option>
                      {Object.entries(SUPPORTED_LANGUAGES).map(([code, name]) => (
                        <option key={code} value={code}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">Target Language *</label>
                    <select
                      value={targetLanguage}
                      onChange={(e) => setTargetLanguage(e.target.value)}
                      className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    >
                      {Object.entries(SUPPORTED_LANGUAGES).map(([code, name]) => (
                        <option key={code} value={code}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <button
                  onClick={uploadVideo}
                  disabled={!selectedFile || isUploading}
                  className="w-full flex items-center justify-center space-x-3 px-8 py-4 bg-orange-500 text-white rounded-lg font-semibold hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-lg"
                >
                  {isUploading ? (
                    <>
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                      <span>Uploading...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-6 h-6" />
                      <span>Upload Video</span>
                    </>
                  )}
                </button>
              </div>
            ) : !jobStatus ? (
              /* ready to process section */
              <div className="space-y-8">
                {/* file info - using reusable component */}
                {fileInfo && (
                  <FileInfoSection
                    fileInfo={fileInfo}
                    title="File Uploaded Successfully"
                    icon={FileText}
                    gradientFrom="blue-50"
                    gradientTo="indigo-50"
                    borderColor="blue-200"
                    iconColor="blue"
                    formatFileSize={formatFileSize}
                    formatDuration={formatDuration}
                    getFileExtension={getFileExtension}
                    getAspectRatio={getAspectRatio}
                    getEstimatedBitrate={getEstimatedBitrate}
                  />
                )}

                <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-4 text-lg">Language Settings</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="text-gray-500 block text-sm">Source Language</span>
                      <span className="text-gray-900 font-medium">
                        {sourceLanguage ? SUPPORTED_LANGUAGES[sourceLanguage as keyof typeof SUPPORTED_LANGUAGES] : 'Auto-detect'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-sm">Target Language</span>
                      <span className="text-gray-900 font-medium">
                        {SUPPORTED_LANGUAGES[targetLanguage as keyof typeof SUPPORTED_LANGUAGES]}
                      </span>
                    </div>
                  </div>
                </div>

                {/* process button */}
                <button
                  onClick={() => startProcessing(jobId)}
                  disabled={isProcessing}
                  className="w-full flex items-center justify-center space-x-3 px-8 py-4 bg-orange-500 text-white rounded-lg font-semibold hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-lg"
                >
                  {isProcessing ? (
                    <>
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                      <span>Starting Processing...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-6 h-6" />
                      <span>Start Processing</span>
                    </>
                  )}
                </button>

                {/* back button */}
                <button
                  onClick={resetForm}
                  className="w-full px-8 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium border border-gray-300"
                >
                  Upload Different Video
                </button>
              </div>
            ) : (
              /* processing section */
              <div className="space-y-8">
                {/* file info - using same reusable component with different styling */}
                {fileInfo && (
                  <FileInfoSection
                    fileInfo={fileInfo}
                    title="File Information"
                    icon={CheckCircle}
                    gradientFrom="green-50"
                    gradientTo="emerald-50"
                    borderColor="green-200"
                    iconColor="green"
                    formatFileSize={formatFileSize}
                    formatDuration={formatDuration}
                    getFileExtension={getFileExtension}
                    getAspectRatio={getAspectRatio}
                    getEstimatedBitrate={getEstimatedBitrate}
                  />
                )}

                {/* progress */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900 text-lg">Processing Progress</h3>
                    <span className="text-orange-500 font-bold text-lg">{jobStatus.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-orange-500 h-3 rounded-full transition-all duration-500"
                      style={{ width: `${jobStatus.progress}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {jobStatus.status === "completed" ? (
                      <CheckCircle className="w-6 h-6 text-green-500" />
                    ) : jobStatus.status === "failed" ? (
                      <AlertCircle className="w-6 h-6 text-red-500" />
                    ) : jobStatus.status === "transcription_complete" ? (
                      <FileText className="w-6 h-6 text-blue-500" />
                    ) : (
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-orange-500"></div>
                    )}
                    <span className="text-gray-600">
                      {jobStatus.status === "transcription_complete" 
                        ? "Transcription complete - Please review and edit if needed"
                        : (jobStatus.message || jobStatus.status)
                      }
                    </span>
                  </div>
                </div>

                {/* download button */}
                {jobStatus.status === "completed" && (
                  <button
                    onClick={downloadVideo}
                    className="w-full flex items-center justify-center space-x-3 px-8 py-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold text-lg"
                  >
                    <Download className="w-6 h-6" />
                    <span>Download Video with Subtitles</span>
                  </button>
                )}

                {/* reset button */}
                <button
                  onClick={resetForm}
                  className="w-full px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Process Another Video
                </button>
              </div>
            )}

            {/* error message */}
            {error && (
              <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-5 h-5 text-red-500" />
                  <span className="text-red-700">{error}</span>
                </div>
              </div>
            )}

            {/* transcription editing */}
            {isEditingTranscription && transcription && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
                  <div className="p-6 border-b border-gray-200">
                    <h3 className="text-xl font-bold text-gray-900 mb-2">Review and Edit Transcription</h3>
                    <p className="text-gray-600">
                      Please review the transcription below and make any necessary corrections before continuing.
                    </p>
                  </div>
                  
                  <div className="p-6 overflow-y-auto max-h-[60vh]">
                    <div className="space-y-4">
                      {transcription.segments.map((segment: any, index: number) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-500">
                              {Math.floor(segment.start / 60)}:{(segment.start % 60).toFixed(1).padStart(4, '0')} - {Math.floor(segment.end / 60)}:{(segment.end % 60).toFixed(1).padStart(4, '0')}
                            </span>
                          </div>
                          <textarea
                            value={segment.text}
                            onChange={(e) => updateTranscriptionSegment(index, e.target.value)}
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                            rows={2}
                            placeholder="Edit transcription text..."
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="p-6 border-t border-gray-200 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        <p><strong>Detected Language:</strong> {transcription.detected_language}</p>
                      </div>
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => {
                            setIsEditingTranscription(false)
                            setTranscription(null)
                          }}
                          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => continueWithTranscription(transcription)}
                          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
                        >
                          Continue Processing
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* video preview section */}
        {jobStatus?.status === "completed" && (
          <div className="max-w-6xl mx-auto mt-8">
            <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-gray-900">Video Preview</h3>
                <button
                  onClick={() => setShowVideoPreview(!showVideoPreview)}
                  className="flex items-center space-x-2 px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors font-medium"
                >
                  <Eye className="w-5 h-5" />
                  <span>{showVideoPreview ? "Hide Preview" : "Show Preview"}</span>
                </button>
              </div>
              {showVideoPreview && (
                <div className="flex justify-center">
                  <div className="w-full max-w-4xl space-y-4">
                    <h4 className="font-semibold text-gray-700 flex items-center justify-center space-x-2 text-lg">
                      <FileText className="w-5 h-5" />
                      <span>Video with Subtitles</span>
                    </h4>
                    <div className="bg-black rounded-lg overflow-hidden">
                      <video
                        controls
                        className="w-full h-auto max-h-96 object-contain"
                        src={`http://localhost:8000/video/preview/${jobId}`}
                        preload="metadata"
                      >
                        Your browser does not support the video tag.
                      </video>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  )
  
}
