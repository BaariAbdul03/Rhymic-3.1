import React from 'react';
import styles from './FullScreenPlayer.module.css';
import { useMusicStore } from '../store/musicStore';
import { useUIStore } from '../store/uiStore';
import { Play, Pause, SkipBack, SkipForward, Shuffle, Repeat, ChevronDown, Heart } from 'lucide-react';

const formatTime = (time) => {
  if (isNaN(time)) return '0:00';
  const minutes = Math.floor(time / 60);
  const seconds = Math.floor(time % 60);
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
};

const FullScreenPlayer = () => {
  const { closePlayer } = useUIStore();
  const { 
    currentSong, isPlaying, togglePlay, nextSong, prevSong, 
    currentTime, duration, seek, shuffle, toggleShuffle, repeat, toggleRepeat,
    toggleLike, likedSongs
  } = useMusicStore();

  if (!currentSong) return null;

  const isLiked = likedSongs.includes(currentSong.id);
  const progress = duration ? (currentTime / duration) * 100 : 0;

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const p = Math.max(0, Math.min(1, x / rect.width));
    seek(p * duration);
  };

  return (
    <div className={styles.fullScreenContainer}>
      <div className={styles.header}>
        <button className={styles.closeButton} onClick={closePlayer}>
          <ChevronDown size={28} />
        </button>
        <h4>Now Playing</h4>
        <div style={{width: 28}}></div> 
      </div>

      <div className={styles.artWrapper}>
        <img src={currentSong.cover} alt={currentSong.title} className={styles.art} />
      </div>

      <div className={styles.info}>
        <div className={styles.titles}>
          <h2 className={styles.title}>{currentSong.title}</h2>
          <p className={styles.artist}>{currentSong.artist}</p>
        </div>
        <button 
          className={`${styles.secondaryControl} ${isLiked ? styles.active : ''}`}
          onClick={() => toggleLike(currentSong.id)}
        >
          <Heart size={24} fill={isLiked ? 'currentColor' : 'none'} />
        </button>
      </div>

      <div className={styles.progressContainer}>
        <div className={styles.progressBar} onClick={handleSeek}>
          <div className={styles.progressFill} style={{width: `${progress}%`}}></div>
        </div>
        <div className={styles.timestamps}>
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>

      <div className={styles.controls}>
        <button 
          className={`${styles.secondaryControl} ${shuffle ? styles.active : ''}`}
          onClick={toggleShuffle}
        >
          <Shuffle size={24} />
        </button>
        
        <button className={styles.secondaryControl} onClick={prevSong}>
          <SkipBack size={32} />
        </button>

        <button className={styles.playButton} onClick={togglePlay}>
          {isPlaying ? <Pause size={32} /> : <Play size={32} fill="currentColor" />}
        </button>

        <button className={styles.secondaryControl} onClick={nextSong}>
          <SkipForward size={32} />
        </button>

        <button 
          className={`${styles.secondaryControl} ${repeat ? styles.active : ''}`}
          onClick={toggleRepeat}
        >
          <Repeat size={24} />
        </button>
      </div>
    </div>
  );
};

export default FullScreenPlayer;