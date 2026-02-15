import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { videosAPI, foldersAPI } from '../services/api';
import Header from '../components/Layout/Header';
import Sidebar from '../components/Layout/Sidebar';
import VideoGrid from '../components/Video/VideoGrid';
import VideoUpload from '../components/Video/VideoUpload';
import VideoContextMenu from '../components/Video/VideoContextMenu';
import MoveVideoModal from '../components/Video/MoveVideoModal';
import VideoPlayer from '../components/Video/VideoPlayer';

export default function DashboardPage() {
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [contextMenu, setContextMenu] = useState(null);
  const [moveVideo, setMoveVideo] = useState(null);
  const [playingVideo, setPlayingVideo] = useState(null);

  const queryClient = useQueryClient();

  const { data: videos, refetch: refetchVideos } = useQuery({
    queryKey: ['videos'],
    queryFn: () => videosAPI.list().then(res => res.data),
    refetchInterval: 5000, // Her 5 saniyede bir yenile (status güncellemeleri için)
  });

  const { data: folders, refetch: refetchFolders } = useQuery({
    queryKey: ['folders'],
    queryFn: () => foldersAPI.list().then(res => res.data),
  });

  // Video silme mutation
  const deleteMutation = useMutation({
    mutationFn: (videoId) => videosAPI.delete(videoId),
    onSuccess: () => {
      queryClient.invalidateQueries(['videos']);
    },
    onError: (error) => {
      alert('Video silinirken bir hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  });

  // Video taşıma mutation
  const moveMutation = useMutation({
    mutationFn: ({ videoId, folderId }) => videosAPI.update(videoId, { folder_id: folderId }),
    onSuccess: () => {
      queryClient.invalidateQueries(['videos']);
      setMoveVideo(null);
    }
  });


  const handleCreateFolder = async (name) => {
    await foldersAPI.create(name);
    refetchFolders();
  };

  const handleVideoContextMenu = (e, video) => {
    e.preventDefault();
    setContextMenu({
      video,
      position: { x: e.clientX, y: e.clientY }
    });
  };

  const filteredVideos = videos?.filter(video => {
    if (!selectedFolder) return true;
    return video.folder_id === selectedFolder.id;
  }) || [];

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 transition-colors">
      {/* Sidebar */}
      <Sidebar
        folders={folders || []}
        onFolderSelect={setSelectedFolder}
        onCreateFolder={handleCreateFolder}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header onSearch={setSearchQuery} />

        {/* Content */}
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 mb-8">
              <div>
                <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100 flex items-center gap-3 transition-colors">
                  {selectedFolder ? selectedFolder.name : 'Tüm Videolar'}
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
                    {filteredVideos.length} video
                  </span>
                  {videos && (
                    <span className="text-gray-400 dark:text-gray-500">
                      • {videos.filter(v => v.status === 'COMPLETED').length} tamamlandı
                    </span>
                  )}
                </p>
              </div>
              <VideoUpload onSuccess={refetchVideos} />
            </div>

            <VideoGrid 
              videos={filteredVideos} 
              onVideoContextMenu={handleVideoContextMenu}
              onRetry={() => refetchVideos()}
            />
          </div>
        </div>
      </div>

      {/* Video Context Menu */}
      {contextMenu && (
        <VideoContextMenu
          video={contextMenu.video}
          position={contextMenu.position}
          onClose={() => setContextMenu(null)}
          onPlay={(video) => setPlayingVideo(video)}
          onMove={(video) => setMoveVideo(video)}
          onDelete={(video) => deleteMutation.mutate(video.id)}
        />
      )}

      {/* Move Video Modal */}
      {moveVideo && (
        <MoveVideoModal
          video={moveVideo}
          folders={folders || []}
          onClose={() => setMoveVideo(null)}
          onSubmit={(videoId, folderId) => moveMutation.mutateAsync({ videoId, folderId })}
        />
      )}

      {/* Video Player */}
      {playingVideo && (
        <VideoPlayer
          video={playingVideo}
          onClose={() => setPlayingVideo(null)}
        />
      )}
    </div>
  );
}
