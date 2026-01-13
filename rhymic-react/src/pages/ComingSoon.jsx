import React from 'react';
import { Link } from 'react-router-dom';
import './ComingSoon.css';

const ComingSoon = () => {
  return (
    <div className="coming-soon-container">
      <h1 className="coming-soon-title">Coming Soon</h1>
      <p className="coming-soon-text">
        The Subscription feature is currently in development. Check back in future updates!
      </p>
      <Link to="/" className="back-link">
        Back to Library
      </Link>
    </div>
  );
};

export default ComingSoon;