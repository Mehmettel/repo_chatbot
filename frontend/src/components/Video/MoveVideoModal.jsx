import { X, FolderInput, Video } from 'lucide-react';
import { useState } from 'react';

export default function MoveVideoModal({ video, folders, onClose, onSubmit }) {
  const [folderId, setFolderId] = useState(video?.folder_id || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!folderId) return;

    setLoading(true);
    try {
      await onSubmit(video.id, folderId);
      onClose();
    } catch (error) {
      console.error('Move error:', error);
      alert('Video taşınırken bir hata oluştu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const renderFolderOption = (folder, level = 0) => {
    return (
      <option key={folder.id} value={folder.id}>
        {'  '.repeat(level)}📁 {folder.name}
      </option>
    );
  };

  const renderFolderTree = (parentId = null, level = 0) => {
    return folders
      .filter(f => f.parent_id === parentId)
      .map(f => [
        renderFolderOption(f, level),
        ...renderFolderTree(f.id, level + 1)
      ])
      .flat();
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <FolderInput size={20} className="text-primary" />
            </div>
            <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
              Videoyu Taşı
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
              <Video size={20} className="text-blue-600 dark:text-blue-400 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900 dark:text-blue-200 line-clamp-2">
                  {video.description_ai?.substring(0, 80) || 'Video'}{video.description_ai?.length > 80 ? '...' : ''}
                </p>
                <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                  Bu video başka bir klasöre taşınacak
                </p>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Hedef Klasör
            </label>
            <select
              value={folderId}
              onChange={(e) => setFolderId(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary dark:bg-gray-700 dark:text-gray-100 transition"
              required
            >
              <option value="">Klasör seçin...</option>
              {renderFolderTree()}
            </select>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
            >
              İptal
            </button>
            <button
              type="submit"
              disabled={loading || !folderId}
              className="flex-1 px-4 py-3 bg-primary text-white rounded-lg hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
            >
              {loading ? 'Taşınıyor...' : 'Taşı'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
