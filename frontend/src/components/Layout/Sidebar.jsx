import { Folder, Plus } from 'lucide-react';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { foldersAPI } from '../../services/api';
import FolderTree from '../Folder/FolderTree';
import FolderContextMenu from '../Folder/FolderContextMenu';
import RenameFolderModal from '../Folder/RenameFolderModal';
import MoveFolderModal from '../Folder/MoveFolderModal';

export default function Sidebar({ folders = [], onFolderSelect, onCreateFolder }) {
  const [isCreating, setIsCreating] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [renameFolder, setRenameFolder] = useState(null);
  const [moveFolder, setMoveFolder] = useState(null);

  const queryClient = useQueryClient();

  const handleCreate = async () => {
    if (!newFolderName.trim()) return;
    
    try {
      await onCreateFolder(newFolderName);
      setNewFolderName('');
      setIsCreating(false);
    } catch (err) {
      console.error('Folder creation failed:', err);
    }
  };

  const handleSelect = (folder) => {
    setSelectedId(folder?.id || null);
    onFolderSelect(folder);
  };

  const handleContextMenu = (e, folder) => {
    e.preventDefault();
    setContextMenu({
      folder,
      position: { x: e.clientX, y: e.clientY }
    });
  };

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (folderId) => foldersAPI.delete(folderId),
    onSuccess: () => {
      queryClient.invalidateQueries(['folders']);
      if (selectedId === contextMenu?.folder?.id) {
        setSelectedId(null);
        onFolderSelect(null);
      }
    },
    onError: (error) => {
      alert('Klasör silinirken bir hata oluştu: ' + (error.response?.data?.detail || error.message));
    }
  });

  // Rename mutation
  const renameMutation = useMutation({
    mutationFn: ({ folderId, name }) => foldersAPI.update(folderId, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries(['folders']);
      setRenameFolder(null);
    }
  });

  // Move mutation
  const moveMutation = useMutation({
    mutationFn: ({ folderId, parentId }) => foldersAPI.update(folderId, { parent_id: parentId }),
    onSuccess: () => {
      queryClient.invalidateQueries(['folders']);
      setMoveFolder(null);
    }
  });

  return (
    <>
      <div className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 h-full flex flex-col transition-colors">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-800 dark:text-gray-100">Klasörler</h2>
            <button
              onClick={() => setIsCreating(!isCreating)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition"
              title="Yeni Klasör"
            >
              <Plus size={20} className="text-gray-600 dark:text-gray-300" />
            </button>
          </div>

          {isCreating && (
            <div className="mt-3 flex gap-2">
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                placeholder="Klasör adı"
                className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                autoFocus
              />
              <button
                onClick={handleCreate}
                className="px-3 py-2 bg-primary text-white rounded-lg text-sm hover:bg-opacity-90"
              >
                Ekle
              </button>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-auto p-2">
          <FolderTree
            folders={folders}
            onSelect={handleSelect}
            selectedId={selectedId}
            onContextMenu={handleContextMenu}
          />
        </div>
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <FolderContextMenu
          folder={contextMenu.folder}
          position={contextMenu.position}
          onClose={() => setContextMenu(null)}
          onRename={(folder) => setRenameFolder(folder)}
          onDelete={(folder) => deleteMutation.mutate(folder.id)}
          onMove={(folder) => setMoveFolder(folder)}
        />
      )}

      {/* Rename Modal */}
      {renameFolder && (
        <RenameFolderModal
          folder={renameFolder}
          onClose={() => setRenameFolder(null)}
          onSubmit={(folderId, name) => renameMutation.mutateAsync({ folderId, name })}
        />
      )}

      {/* Move Modal */}
      {moveFolder && (
        <MoveFolderModal
          folder={moveFolder}
          folders={folders}
          onClose={() => setMoveFolder(null)}
          onSubmit={(folderId, parentId) => moveMutation.mutateAsync({ folderId, parentId })}
        />
      )}
    </>
  );
}
