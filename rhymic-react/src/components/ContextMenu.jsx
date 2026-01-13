import React, { useEffect, useRef } from 'react';
import styles from './ContextMenu.module.css';
import { useMusicStore } from '../store/musicStore';
import { Play, ListPlus, ListEnd, User } from 'lucide-react';

const ContextMenu = ({ x, y, song, onClose }) => {
  const menuRef = useRef(null);
  const addToQueue = useMusicStore((state) => state.addToQueue);
  const playNext = useMusicStore((state) => state.playNext);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    // Adjust position if it goes offscreen (basic check)
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  if (!song) return null;

  return (
    <div 
      className={styles.menu} 
      style={{ top: y, left: x }} 
      ref={menuRef}
    >
      <button className={styles.menuItem} onClick={() => { playNext(song); onClose(); }}>
        <ListPlus size={16} /> Play Next
      </button>
      <button className={styles.menuItem} onClick={() => { addToQueue(song); onClose(); }}>
        <ListEnd size={16} /> Add to Queue
      </button>
      {/* 
      <button className={styles.menuItem} onClick={() => { alert(`Go to ${song.artist}`); onClose(); }}>
        <User size={16} /> Go to Artist
      </button>
      */}
    </div>
  );
};

export default ContextMenu;