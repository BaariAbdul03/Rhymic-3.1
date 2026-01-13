// src/store/authStore.js
import { create } from 'zustand';

export const useAuthStore = create((set, get) => ({
  user: JSON.parse(localStorage.getItem('user')) || null,
  token: localStorage.getItem('token') || null,
  error: null,

  login: async (email, password) => {
    set({ error: null });
    try {
      const response = await fetch('/api/login', { // Use relative path
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Login failed due to an unknown error.');
      }

      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));

      set({ user: data.user, token: data.token });
      return true;
    } catch (err) {
      set({ error: err.message });
      return false;
    }
  },

  signup: async (name, email, password) => {
    set({ error: null });
    try {
      const response = await fetch('/api/signup', { // Use relative path
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || 'Signup failed due to an unknown error.');
      }
      return true;
    } catch (err) {
      set({ error: err.message });
      return false;
    }
  },

  fetchUser: async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const response = await fetch('/api/user/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.status === 404 || response.status === 401) {
        // User not found (DB reset) or invalid token -> Force Logout
        get().logout();
        return;
      }

      if (response.ok) {
        const userData = await response.json();
        localStorage.setItem('user', JSON.stringify(userData));
        set({ user: userData });
      }
    } catch (error) {
      console.error("Failed to fetch user", error);
    }
  },

  uploadProfilePic: async (file) => {
    const token = localStorage.getItem('token');
    if (!token) return false;
    
    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch('/api/user/upload_profile_pic', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }, // No Content-Type for FormData
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        // Update state
        set((state) => {
          const newUser = { ...state.user, profile_pic: data.profile_pic };
          localStorage.setItem('user', JSON.stringify(newUser));
          return { user: newUser };
        });
        return true;
      }
    } catch (error) {
      console.error("Upload failed", error);
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    set({ user: null, token: null });
  }
}));