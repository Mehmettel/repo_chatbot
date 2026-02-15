import { useState } from 'react';
import { Video, Plus } from 'lucide-react';
import VideoCard from './VideoCard';
import VideoPlayer from './VideoPlayer';

export default function VideoGrid({ videos = [], onVideoContextMenu, onRetry }) {
  const [selectedVideo, setSelectedVideo] = useState(null);

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32 px-4">
        <div className="w-24 h-24 bg-gradient-to-br from-primary/20 to-secondary/20 rounded-full flex items-center justify-center mb-6">
          <Video size={48} className="text-primary/60" />
        </div>
        <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-200 mb-2">
          Henüz video yok
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center max-w-md">
          Sağ üstteki <span className="inline-flex items-center gap-1 font-medium text-primary">
            <Plus size={14} /> Video Ekle
          </span> butonunu kullanarak ilk videonuzu ekleyin
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
        {videos.map((video) => (
          <VideoCard
            key={video.id}
            video={video}
            onClick={() => setSelectedVideo(video)}
            onContextMenu={onVideoContextMenu}
            onRetry={onRetry}
          />
        ))}
      </div>

      {selectedVideo && (
        <VideoPlayer
          video={selectedVideo}
          onClose={() => setSelectedVideo(null)}
        />
      )}
    </>
  );
}
