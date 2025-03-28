import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout, isAdmin } = useAuth();
  const [greeting, setGreeting] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const hours = new Date().getHours();
    let greetingText = '';
    
    if (hours < 12) {
      greetingText = 'Good morning';
    } else if (hours < 18) {
      greetingText = 'Good afternoon';
    } else {
      greetingText = 'Good evening';
    }
    
    setGreeting(greetingText);
  }, []);

  if (!user) {
    return <div>Loading user information...</div>;
  }

  // Function to get a user-friendly role name with capitalization
  const getRoleName = (role) => {
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  const goToAdminPanel = () => {
    navigate('/admin/users');
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>{greeting}, {user.full_name || user.username}!</h2>
        <button className="logout-btn" onClick={logout}>Logout</button>
      </div>
      
      <div className="dashboard-content">
        <div className="user-profile-card">
          <h3>User Profile</h3>
          <div className="profile-details">
            <p><strong>Username:</strong> {user.username}</p>
            <p><strong>Email:</strong> {user.email}</p>
            {user.full_name && <p><strong>Full Name:</strong> {user.full_name}</p>}
            <p><strong>Role:</strong> <span className={`role-badge ${user.role}`}>{getRoleName(user.role)}</span></p>
          </div>
        </div>
        
        <div className="dashboard-actions">
          <h3>Quick Actions</h3>
          <div className="action-buttons">
            <button>Edit Profile</button>
            <button>Change Password</button>
            {isAdmin() && <button className="admin-button" onClick={goToAdminPanel}>Admin Panel</button>}
          </div>
        </div>
        
        {isAdmin() && (
          <div className="admin-section">
            <h3>Admin Actions</h3>
            <div className="action-buttons">
              <button onClick={goToAdminPanel}>Manage Users</button>
              <button>View System Logs</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 