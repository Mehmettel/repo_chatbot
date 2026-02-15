import { Play, Clock, CheckCircle, XCircle, Loader, MoreVertical, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { videosAPI } from '../../services/api';

export default function VideoCard({ video, onClick, onContextMenu, onRetry }) {
  const [isRetrying, setIsRetrying] = useState(false);
  const statusConfig = {
    COMPLETED: { 
      icon: <CheckCircle size={16} />,
      text: 'Tamamlandı',
      bgColor: 'bg-green-100',
      textColor: 'text-green-700',
      iconColor: 'text-green-600'
    },
    PROCESSING: { 
      icon: <Loader className="animate-spin" size={16} />,
      text: 'İşleniyor',
      bgColor: 'bg-blue-100',
      textColor: 'text-blue-700',
      iconColor: 'text-blue-600'
    },
    FAILED: { 
      icon: <XCircle size={16} />,
      text: 'Başarısız',
      bgColor: 'bg-red-100',
      textColor: 'text-red-700',
      iconColor: 'text-red-600'
    },
    PENDING: { 
      icon: <Clock size={16} />,
      text: 'Bekliyor',
      bgColor: 'bg-yellow-100',
      textColor: 'text-yellow-700',
      iconColor: 'text-yellow-600'
    },
  };

  const status = statusConfig[video.status] || statusConfig.PENDING;

  const formatDuration = (seconds) => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Markdown ve gereksiz karakterleri temizle
  const cleanDescription = (text) => {
    if (!text) return 'Video işleniyor...';
    return text
      .replace(/#{1,6}\s?/g, '') // Markdown başlıkları
      .replace(/\*\*/g, '') // Bold
      .replace(/\*/g, '') // Italic
      .replace(/###/g, '') // Kalan ###
      .replace(/\n+/g, ' ') // Yeni satırlar
      .replace(/\s+/g, ' ') // Fazla boşluklar
      .trim();
  };

  // Kısa özet oluştur
  const getShortSummary = (text) => {
    const cleaned = cleanDescription(text);
    // İlk cümleyi al veya 80 karaktere kadar kes
    const firstSentence = cleaned.split(/[.!?]\s/)[0];
    if (firstSentence.length > 80) {
      return firstSentence.substring(0, 80) + '...';
    }
    return firstSentence + (cleaned.length > firstSentence.length ? '...' : '');
  };

  const displayTitle = video.title || 'Video İçeriği';

  const handleContextMenu = (e) => {
    e.preventDefault();
    if (onContextMenu) {
      onContextMenu(e, video);
    }
  };

  const handleMenuClick = (e) => {
    e.stopPropagation();
    // Sağ tıklama menüsünü açmak için fake event oluştur
    if (onContextMenu) {
      const rect = e.currentTarget.getBoundingClientRect();
      onContextMenu({ clientX: rect.right, clientY: rect.top, preventDefault: () => {} }, video);
    }
  };

  const handleRetry = async (e) => {
    e.stopPropagation();
    if (isRetrying) return;
    
    setIsRetrying(true);
    try {
      await videosAPI.retry(video.id);
      if (onRetry) {
        onRetry(video.id);
      }
    } catch (err) {
      console.error('Retry hatası:', err);
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <div 
      onClick={() => video.status === 'COMPLETED' && onClick()}
      onContextMenu={handleContextMenu}
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-md hover:shadow-xl dark:shadow-gray-900/50 transition-all duration-300 overflow-hidden group relative ${
        video.status === 'COMPLETED' ? 'cursor-pointer hover:scale-[1.02]' : 'opacity-75'
      }`}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
        {video.status === 'COMPLETED' ? (
          <>
            {/* Gradient Placeholder Background */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/30 via-purple-500/20 to-secondary/30"></div>
            
            {/* Icon + Title Placeholder */}
            <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
              <Play size={64} className="text-white/90 mb-3 drop-shadow-lg" strokeWidth={1.5} />
              <p className="text-white text-sm font-bold line-clamp-2 drop-shadow-lg px-4">
                {displayTitle}
              </p>
            </div>
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-200 dark:from-gray-700 to-gray-300 dark:to-gray-800">
            <div className="text-center">
              <div className={status.iconColor}>{status.icon}</div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 font-medium">{status.text}</p>
              
              {/* Yeniden Dene butonu - PENDING ve FAILED için */}
              {(video.status === 'PENDING' || video.status === 'FAILED') && (
                <button
                  onClick={handleRetry}
                  disabled={isRetrying}
                  className="mt-3 px-4 py-2 bg-primary hover:bg-primary/90 text-white text-sm font-medium rounded-lg flex items-center gap-2 mx-auto transition-all disabled:opacity-50"
                >
                  <RefreshCw size={14} className={isRetrying ? 'animate-spin' : ''} />
                  {isRetrying ? 'İşleniyor...' : 'Yeniden Dene'}
                </button>
              )}
            </div>
          </div>
        )}
        
        {/* Play overlay - sadece COMPLETED için */}
        {video.status === 'COMPLETED' && (
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-all duration-300 flex items-center justify-center">
            <div className="transform scale-0 group-hover:scale-110 transition-transform duration-300">
              <div className="bg-white rounded-full p-5 shadow-2xl">
                <Play size={40} className="text-primary" fill="currentColor" />
              </div>
            </div>
          </div>
        )}

        {/* Badges container */}
        <div className="absolute bottom-2 right-2 flex flex-col items-end gap-1.5">
          {/* Transcript badge */}
          {video.transcript && (
            <div className="bg-blue-600/90 text-white text-xs font-medium px-2 py-0.5 rounded-md backdrop-blur-sm flex items-center gap-1">
              <span>🎙️</span>
            </div>
          )}
          
          {/* Duration badge */}
          {video.duration && (
            <div className="bg-black/80 text-white text-xs font-medium px-2.5 py-1 rounded-md backdrop-blur-sm">
              {formatDuration(video.duration)}
            </div>
          )}
        </div>

        {/* Status badge */}
        <div className={`absolute top-2 left-2 ${status.bgColor} ${status.textColor} text-xs font-medium px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-sm`}>
          <span className={status.iconColor}>{status.icon}</span>
          <span>{status.text}</span>
        </div>

        {/* Menu button - Her zaman görünür */}
        {onContextMenu && (
          <button
            onClick={handleMenuClick}
            className="absolute top-2 right-2 p-2 bg-black/60 hover:bg-black/90 text-white rounded-full transition-all shadow-lg backdrop-blur-sm hover:scale-110 active:scale-95"
            title="Menü"
          >
            <MoreVertical size={18} />
          </button>
        )}
      </div>

      {/* Info */}
      <div className="p-4">
        {/* Video Başlığı */}
        <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 line-clamp-1 mb-2">
          {displayTitle}
        </h3>
        
        {/* Kısa Özet */}
        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 min-h-[2.5rem] leading-relaxed">
          {getShortSummary(video.description_ai)}
        </p>
        
        {/* Meta Bilgiler */}
        <div className="mt-3 flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
          <span className="flex items-center gap-2">
            <span className="text-gray-500 dark:text-gray-400">📅</span>
            {video.created_at 
              ? new Date(video.created_at).toLocaleDateString('tr-TR', { 
                  day: 'numeric', 
                  month: 'short',
                  year: 'numeric'
                })
              : 'Tarih yok'
            }
          </span>
          {video.source_url && (
            <span className="truncate ml-2 max-w-[100px] text-primary/70" title={video.source_url}>
              {(() => {
                try {
                  return new URL(video.source_url).hostname.replace('www.', '');
                } catch {
                  return 'video';
                }
              })()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
