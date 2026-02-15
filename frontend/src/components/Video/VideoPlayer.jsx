import { X, Download, ExternalLink } from 'lucide-react';
import { useEffect } from 'react';

export default function VideoPlayer({ video, onClose }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  // Markdown karakterlerini temizle
  const cleanDescription = (text) => {
    if (!text) return 'Video açıklaması henüz oluşturulmadı.';
    return text
      .replace(/#{1,6}\s?/g, '') // Markdown başlıkları
      .replace(/\*\*/g, '') // Bold
      .replace(/\*/g, '') // Italic
      .replace(/###/g, '') // Kalan ###
      .trim();
  };

  const handleDownload = async (e) => {
    e.preventDefault();
    if (!video.playback_url) return;
    
    try {
      // Fetch video as blob
      const response = await fetch(video.playback_url);
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `video_${video.id}.mp4`;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback: open in new tab
      window.open(video.playback_url, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 line-clamp-1 flex-1 mr-4">
            Video Oynatıcı
          </h3>
          <div className="flex items-center gap-2">
            {video.playback_url && (
              <>
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-opacity-90 transition-all shadow-sm hover:shadow-md"
                  title="İndir"
                >
                  <Download size={18} />
                  <span className="text-sm font-medium">İndir</span>
                </button>
                <a
                  href={video.playback_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition"
                  title="Yeni sekmede aç"
                >
                  <ExternalLink size={20} className="text-gray-600 dark:text-gray-300" />
                </a>
              </>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition"
              title="Kapat (ESC)"
            >
              <X size={20} className="text-gray-600 dark:text-gray-300" />
            </button>
          </div>
        </div>

        {/* Video Player */}
        <div className="bg-black flex-shrink-0">
          {video.playback_url ? (
            <video
              src={video.playback_url}
              controls
              autoPlay
              className="w-full max-h-[60vh] object-contain"
            >
              Tarayıcınız video etiketini desteklemiyor.
            </video>
          ) : (
            <div className="flex items-center justify-center h-64 text-white">
              <div className="text-center">
                <X size={48} className="mx-auto mb-2 opacity-50" />
                <p>Video yüklenemedi</p>
              </div>
            </div>
          )}
        </div>

        {/* Info - Scrollable */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gray-50 dark:bg-gray-900">
          {/* Title */}
          {video.title && (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-2">
                <span className="text-primary">🎬</span> Video Başlığı
              </h4>
              <p className="text-base text-gray-900 dark:text-gray-100 font-medium">
                {video.title}
              </p>
            </div>
          )}

          {/* AI Description */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
            <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
              <span className="text-primary text-xl">✨</span> 
              <span>AI Görsel Analizi</span>
              <span className="ml-2 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full">
                GPT-4o Multi-Frame
              </span>
            </h4>
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
              {cleanDescription(video.description_ai)}
            </p>
          </div>

          {/* Transcript */}
          {video.transcript && (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-4 shadow-sm border border-blue-100 dark:border-blue-800">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2 flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">🎙️</span> Ses Transkripti (Whisper AI)
              </h4>
              <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed italic bg-white/50 dark:bg-gray-900/30 rounded p-3">
                "{video.transcript}"
              </p>
            </div>
          )}

          {/* Video Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Süre</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {video.duration 
                  ? `${Math.floor(video.duration / 60)}:${(video.duration % 60).toString().padStart(2, '0')}`
                  : 'Bilinmiyor'
                }
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Eklenme Tarihi</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {new Date(video.created_at).toLocaleDateString('tr-TR', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric'
                })}
              </div>
            </div>
          </div>

          {/* Source URL */}
          {video.source_url && (
            <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Kaynak</div>
              <a 
                href={video.source_url} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-sm text-primary hover:underline break-all flex items-center gap-2"
              >
                <ExternalLink size={14} />
                {video.source_url}
              </a>
            </div>
          )}

          {/* Search Score (if available) */}
          {video.search_score !== undefined && (
            <div className="bg-gradient-to-r from-primary/10 to-secondary/10 dark:from-primary/20 dark:to-secondary/20 rounded-lg p-4">
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Arama Eşleşme Skoru</div>
              <div className="text-2xl font-bold text-primary">
                {(video.search_score * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                AI semantik benzerlik oranı
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
