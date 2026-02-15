import { X, FolderInput, FolderOpen } from 'lucide-react';
import { useState } from 'react';

export default function MoveFolderModal({ folder, folders, onClose, onSubmit }) {
  const [parentId, setParentId] = useState(folder?.parent_id || null);
  const [loading, setLoading] = useState(false);

  // Mevcut klasör ve alt klasörlerini filtreleyip seçilemez yap
  const getDescendantIds = (folderId, allFolders) => {
    const descendants = [];
    const findDescendants = (id) => {
      descendants.push(id);
      allFolders.filter(f => f.parent_id === id).forEach(child => {
        findDescendants(child.id);
      });
    };
    findDescendants(folderId);
    return descendants;
  };

  const disabledIds = getDescendantIds(folder.id, folders);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit(folder.id, parentId);
      onClose();
    } catch (error) {
      console.error('Move error:', error);
      alert('Klasör taşınırken bir hata oluştu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const renderFolderOption = (f, level = 0) => {
    const isDisabled = disabledIds.includes(f.id);
    return (
      <option 
        key={f.id} 
        value={f.id} 
        disabled={isDisabled}
        className={isDisabled ? 'text-gray-400' : ''}
      >
        {'  '.repeat(level)}📁 {f.name} {isDisabled ? '(seçilemez)' : ''}
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
              Klasörü Taşı
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
              <FolderOpen size={20} className="text-blue-600 dark:text-blue-400 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                  "{folder.name}" klasörü taşınacak
                </p>
                <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                  İçindeki tüm videolar ve alt klasörler birlikte taşınacak
                </p>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Hedef Klasör
            </label>
            <select
              value={parentId || ''}
              onChange={(e) => setParentId(e.target.value || null)}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary dark:bg-gray-700 dark:text-gray-100 transition"
            >
              <option value="">📂 Ana Dizin (Kök)</option>
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
              disabled={loading}
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
