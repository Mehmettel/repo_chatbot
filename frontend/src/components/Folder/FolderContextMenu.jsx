import { Edit2, Trash2, FolderInput } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function FolderContextMenu({ folder, position, onClose, onRename, onDelete, onMove }) {
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

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-1 min-w-[180px]"
      style={{
        top: `${position.y}px`,
        left: `${position.x}px`,
      }}
    >
      <button
        onClick={() => {
          onRename(folder);
          onClose();
        }}
        className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors"
      >
        <Edit2 size={16} />
        Yeniden Adlandır
      </button>

      <button
        onClick={() => {
          onMove(folder);
          onClose();
        }}
        className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 transition-colors"
      >
        <FolderInput size={16} />
        Taşı
      </button>

      <div className="border-t border-gray-200 dark:border-gray-700 my-1"></div>

      <button
        onClick={() => {
          if (confirm(`"${folder.name}" klasörünü silmek istediğinizden emin misiniz? İçindeki tüm videolar etkilenmeyecek.`)) {
            onDelete(folder);
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
