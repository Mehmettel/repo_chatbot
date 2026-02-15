import { Folder, ChevronRight, ChevronDown } from 'lucide-react';
import { useState } from 'react';

export default function FolderTree({ 
  folders = [], 
  onSelect, 
  selectedId, 
  onContextMenu 
}) {
  const [expandedIds, setExpandedIds] = useState(new Set());

  const toggleExpanded = (folderId, e) => {
    e.stopPropagation();
    setExpandedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderId)) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
      }
      return newSet;
    });
  };

  const handleContextMenu = (e, folder) => {
    e.preventDefault();
    e.stopPropagation();
    if (onContextMenu) {
      onContextMenu(e, folder);
    }
  };

  const renderFolder = (folder, level = 0) => {
    const children = folders.filter(f => f.parent_id === folder.id);
    const hasChildren = children.length > 0;
    const isExpanded = expandedIds.has(folder.id);
    const isSelected = selectedId === folder.id;

    return (
      <div key={folder.id} style={{ marginLeft: `${level * 12}px` }}>
        <button
          onClick={() => onSelect(folder)}
          onContextMenu={(e) => handleContextMenu(e, folder)}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg transition group ${
            isSelected 
              ? 'bg-primary text-white' 
              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}
        >
          {hasChildren && (
            <button
              onClick={(e) => toggleExpanded(folder.id, e)}
              className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition"
            >
              {isExpanded ? (
                <ChevronDown size={14} className={isSelected ? 'text-white' : 'text-gray-500'} />
              ) : (
                <ChevronRight size={14} className={isSelected ? 'text-white' : 'text-gray-500'} />
              )}
            </button>
          )}
          {!hasChildren && <span className="w-[18px]" />}
          
          <Folder size={16} className={isSelected ? 'text-white' : 'text-primary'} />
          <span className="text-sm font-medium truncate flex-1 text-left">
            {folder.name}
          </span>
          
          <span className={`text-xs opacity-0 group-hover:opacity-100 transition ${
            isSelected ? 'text-white/70' : 'text-gray-400'
          }`}>
            ⋮
          </span>
        </button>

        {hasChildren && isExpanded && (
          <div className="mt-1">
            {children.map(child => renderFolder(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const rootFolders = folders.filter(f => !f.parent_id);

  return (
    <div className="space-y-1">
      <button
        onClick={() => onSelect(null)}
        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition ${
          selectedId === null 
            ? 'bg-primary text-white' 
            : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
        }`}
      >
        <Folder size={18} />
        <span className="text-sm font-medium">Tüm Videolar</span>
      </button>

      {rootFolders.map(folder => renderFolder(folder))}
    </div>
  );
}
