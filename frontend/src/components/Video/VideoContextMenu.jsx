import { Trash2, FolderInput, Play, Edit2 } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function VideoContextMenu({ video, position, onClose, onPlay, onMove, onDelete, onEdit }) {
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        onClose();
      }
    };

    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  const isReady = video.status === 'COMPLETED';

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-1 min-w-[180px]"
      style={{
        top: `${position.y}px`,
        left: `${position.x}px`,
      }}
    >
      {isReady && (
        <button
          onClick={() => {
            onPlay(video);
            onClose();
          }}
          className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors"
        >
          <Play size={16} />
          Oynat
        </button>
      )}

      <button
        onClick={() => {
          onMove(video);
          onClose();
        }}
        className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors"
      >
        <FolderInput size={16} />
        Başka Klasöre Taşı
      </button>

      {isReady && onEdit && (
        <button
          onClick={() => {
            onEdit(video);
            onClose();
          }}
          className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors"
        >
          <Edit2 size={16} />
          Açıklama Düzenle
        </button>
      )}

      <div className="border-t border-gray-200 dark:border-gray-700 my-1"></div>

      <button
        onClick={() => {
          if (confirm(`Bu videoyu silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.`)) {
            onDelete(video);
            onClose();
          }
        }}
        className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2 transition-colors"
      >
        <Trash2 size={16} />
        Sil
      </button>
    </div>
  );
}
