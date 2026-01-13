// Topbar.jsx
import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import styles from './Topbar.module.css';
import { Search, User } from 'lucide-react';
import { useMusicStore } from '../store/musicStore';
import { useAuthStore } from '../store/authStore';

const Topbar = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isFocused, setIsFocused] = useState(false);
  const searchRef = useRef(null);
  
  const user = useAuthStore((state) => state.user);
  
  // Get songs and actions from the store
  const allSongs = useMusicStore((state) => state.songs);
  const setCurrentSong = useMusicStore((state) => state.setCurrentSong);

  // Filter songs when query changes
  useEffect(() => {
    if (query.trim() === '') {
      setResults([]);
      return;
    }
    
    const filtered = allSongs.filter(song =>
      song.title.toLowerCase().includes(query.toLowerCase()) ||
      song.artist.toLowerCase().includes(query.toLowerCase())
    );
    setResults(filtered);
  }, [query, allSongs]);

  // Handle clicking a search result
  const handleResultClick = (song) => {
    setCurrentSong(song);
    setQuery('');
    setResults([]);
    setIsFocused(false);
  };
  
  // Close results when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsFocused(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const PLACEHOLDER_IMG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='150' height='150' viewBox='0 0 150 150'%3E%3Crect width='150' height='150' fill='%23cccccc'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='Arial' font-size='24' fill='%23666666'%3EUser%3C/text%3E%3C/svg%3E";

  return (
    <nav className={styles.topbar}>
      <div className={styles.searchWrapper} ref={searchRef}>
        <div className={styles.searchContainer}>
          <Search size={18} className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search music, artists..."
            className={styles.searchInput}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
          />
        </div>
        
        {/* Search Results Dropdown */}
        {isFocused && (query.length > 0 || results.length > 0) && (
          <div className={styles.resultsDropdown}>
            {results.length > 0 ? (
              results.map(song => (
                <div 
                  key={song.id} 
                  className={styles.resultItem}
                  onClick={() => handleResultClick(song)}
                >
                  <img src={song.cover} alt={song.title} className={styles.resultCover} />
                  <div className={styles.resultInfo}>
                    <h4>{song.title}</h4>
                    <p>{song.artist}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className={styles.noResults}>No results found</div>
            )}
          </div>
        )}
      </div>

      {/* User/Subscribe Buttons */}
      <div className={styles.userControls}>
        {/* Link to Profile */}
        <Link to="/profile" className={styles.userIcon} style={{padding: 0, overflow:'hidden'}}>
          <img 
            src={user?.profile_pic || PLACEHOLDER_IMG} 
            alt="Profile" 
            style={{width:'100%', height:'100%', objectFit:'cover'}} 
            onError={(e) => { e.target.onerror = null; e.target.src = PLACEHOLDER_IMG; }}
          />
        </Link>
        <Link to="/subscribe" className={styles.subscribeButton}>
          Subscribe
        </Link>
      </div>
    </nav>
  );
};

export default Topbar;