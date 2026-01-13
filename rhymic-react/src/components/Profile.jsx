import React, { useRef, useEffect } from 'react';
import styles from './Profile.module.css';
import { useAuthStore } from '../store/authStore';
import { Camera, Mail, User } from 'lucide-react';

const Profile = () => {
  const user = useAuthStore((state) => state.user);
  const fetchUser = useAuthStore((state) => state.fetchUser);
  const uploadProfilePic = useAuthStore((state) => state.uploadProfilePic);
  
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      await uploadProfilePic(file);
    }
  };

  if (!user) return <div style={{padding: 40, textAlign:'center'}}>Loading Profile...</div>;

  const profilePic = user.profile_pic || 'https://via.placeholder.com/150';

  return (
    <div className={styles.profileContainer}>
      <div className={styles.card}>
        <div className={styles.avatarWrapper} onClick={() => fileInputRef.current.click()}>
          <img 
            src={profilePic} 
            alt="Profile" 
            className={styles.avatar} 
            onError={(e) => { e.target.onerror = null; e.target.src = 'https://via.placeholder.com/150'; }}
          />
          <div className={styles.avatarOverlay}>
            <Camera className={styles.editIcon} />
          </div>
        </div>
        
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          accept="image/*"
          onChange={handleFileChange}
        />

        <h1 className={styles.name}>{user.name}</h1>
        <p className={styles.email}>{user.email}</p>

        <div className={styles.infoGroup}>
          <div style={{marginBottom: 20}}>
            <span className={styles.label}>Username</span>
            <div className={styles.value} style={{display:'flex', alignItems:'center', gap: 10}}>
              <User size={18} /> {user.name}
            </div>
          </div>
          
          <div>
            <span className={styles.label}>Email Address</span>
            <div className={styles.value} style={{display:'flex', alignItems:'center', gap: 10}}>
              <Mail size={18} /> {user.email}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;