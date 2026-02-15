import { Plus, Upload, List, Link2 } from 'lucide-react';
import { useState } from 'react';
import { videosAPI, foldersAPI } from '../../services/api';
import { useQuery } from '@tanstack/react-query';

const MODES = {
  single: 'single',
  bulk: 'bulk',
  playlist: 'playlist',
};

export default function VideoUpload({ onSuccess }) {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState(MODES.single);
  const [url, setUrl] = useState('');
  const [bulkUrls, setBulkUrls] = useState('');
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [maxEntries, setMaxEntries] = useState(50);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const { data: folders } = useQuery({
    queryKey: ['folders'],
    queryFn: () => foldersAPI.list().then(res => res.data),
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!selectedFolder) {
      setError('Lütfen bir klasör seçin');
      return;
    }

    setLoading(true);

    try {
      if (mode === MODES.single) {
        await videosAPI.create(url, selectedFolder);
        setUrl('');
        setSuccessMsg('1 video kuyruğa eklendi');
      } else if (mode === MODES.bulk) {
        const lines = bulkUrls
          .split(/[\n,]+/)
          .map((s) => s.trim())
          .filter((s) => s.startsWith('http'));
        if (lines.length === 0) {
          setError('En az bir geçerli URL girin');
          setLoading(false);
          return;
        }
        const res = await videosAPI.createBulk(lines, selectedFolder);
        setBulkUrls('');
        setSuccessMsg(`${res.data?.created ?? lines.length} video kuyruğa eklendi`);
      } else {
        const res = await videosAPI.createFromPlaylist(
          playlistUrl,
          selectedFolder,
          maxEntries
        );
        setPlaylistUrl('');
        setSuccessMsg(res.data?.message ?? `${res.data?.created ?? 0} video kuyruğa eklendi`);
      }
      setSelectedFolder('');
      if (onSuccess) onSuccess();
      setTimeout(() => {
        setIsOpen(false);
        setSuccessMsg('');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Video eklenemedi');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-lg hover:bg-opacity-90 transition shadow-lg"
      >
        <Plus size={20} />
        <span className="font-medium">Video Ekle</span>
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-2">
            <Upload size={24} className="text-primary" />
            Video Ekle
          </h2>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        {/* Mod seçimi */}
        <div className="flex gap-2 mb-4 p-1 bg-gray-100 dark:bg-gray-700 rounded-lg">
          <button
            type="button"
            onClick={() => setMode(MODES.single)}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition ${
              mode === MODES.single
                ? 'bg-white dark:bg-gray-600 text-primary shadow'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
            }`}
          >
            <Link2 size={16} />
            Tek Video
          </button>
          <button
            type="button"
            onClick={() => setMode(MODES.bulk)}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition ${
              mode === MODES.bulk
                ? 'bg-white dark:bg-gray-600 text-primary shadow'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
            }`}
          >
            <Link2 size={16} />
            Toplu URL
          </button>
          <button
            type="button"
            onClick={() => setMode(MODES.playlist)}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition ${
              mode === MODES.playlist
                ? 'bg-white dark:bg-gray-600 text-primary shadow'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
            }`}
          >
            <List size={16} />
            Playlist
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === MODES.single && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Video URL
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                required
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                YouTube, Instagram, TikTok desteklenir
              </p>
            </div>
          )}

          {mode === MODES.bulk && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Video URL'leri (her satıra bir tane veya virgülle ayırın)
              </label>
              <textarea
                value={bulkUrls}
                onChange={(e) => setBulkUrls(e.target.value)}
                placeholder={'https://youtube.com/watch?v=...\nhttps://youtube.com/watch?v=...\n...'}
                rows={6}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 font-mono text-sm"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                En fazla 100 video. Her satır veya virgülle ayrılmış URL.
              </p>
            </div>
          )}

          {mode === MODES.playlist && (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Playlist URL
                </label>
                <input
                  type="url"
                  value={playlistUrl}
                  onChange={(e) => setPlaylistUrl(e.target.value)}
                  placeholder="https://www.youtube.com/playlist?list=..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  required={mode === MODES.playlist}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  YouTube playlist veya channel linki
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Maksimum video sayısı
                </label>
                <input
                  type="number"
                  min={1}
                  max={100}
                  value={maxEntries}
                  onChange={(e) => setMaxEntries(Math.min(100, Math.max(1, +e.target.value)))}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Klasör
            </label>
            <select
              value={selectedFolder}
              onChange={(e) => setSelectedFolder(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              required
            >
              <option value="">Klasör seçin</option>
              {folders?.map((folder) => (
                <option key={folder.id} value={folder.id}>
                  {folder.name}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}
          {successMsg && (
            <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-400 text-sm">
              {successMsg}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition"
              disabled={loading}
            >
              İptal
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-3 bg-primary text-white rounded-lg hover:bg-opacity-90 transition disabled:bg-gray-400"
              disabled={loading}
            >
              {loading ? 'Ekleniyor...' : mode === MODES.single ? 'Ekle' : 'Toplu Ekle'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
