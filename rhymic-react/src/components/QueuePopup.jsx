import React from 'react';
import styles from './QueuePopup.module.css'; // Updated CSS import
import { useMusicStore } from '../store/musicStore';
import { Play } from 'lucide-react';

const QueuePopup = ({ onClose }) => {
  const songs = useMusicStore((state) => state.songs);
  const currentSong = useMusicStore((state) => state.currentSong);
  const setCurrentSong = useMusicStore((state) => state.setCurrentSong);

  return (
    <div className={styles.queueContainer}>
      <div className={styles.queueHeader}>
        <h3>Playing Next</h3>
        <button onClick={onClose} className={styles.closeButton}>Close</button>
      </div>
      <div className={styles.queueList}>
        {songs.map((song, index) => (
          <div 
            key={index} 
            className={`${styles.queueItem} ${currentSong?.id === song.id ? styles.activeQueue : ''}`}
            onClick={() => setCurrentSong(song)}
          >
            <img src={song.cover} alt="" />
            <div className={styles.queueInfo}>
              <span>{song.title}</span>
              <small>{song.artist}</small>
            </div>
            {currentSong?.id === song.id && <Play size={12} fill="currentColor" color="var(--accent-color)"/>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default QueuePopup;
