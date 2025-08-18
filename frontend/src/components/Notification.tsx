import React, { useEffect, useState } from 'react';
import './Notification.css';

export interface NotificationData {
  id: string;
  type: 'success' | 'error' | 'warning';
  title: string;
  message: string;
  autoClose?: boolean;
  duration?: number;
}

interface NotificationProps {
  notification: NotificationData;
  onClose: (id: string) => void;
}

export const Notification: React.FC<NotificationProps> = ({ notification, onClose }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    // Trigger enter animation
    setTimeout(() => setIsVisible(true), 10);

    // Auto close if enabled
    if (notification.autoClose !== false) {
      const timer = setTimeout(() => {
        handleClose();
      }, notification.duration || 5000);

      return () => clearTimeout(timer);
    }
  }, [notification]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose(notification.id);
    }, 300);
  };

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      default:
        return 'ℹ️';
    }
  };

  return (
    <div 
      className={`notification notification-${notification.type} ${isVisible ? 'visible' : ''} ${isClosing ? 'closing' : ''}`}
    >
      <div className="notification-icon">
        {getIcon()}
      </div>
      <div className="notification-content">
        <div className="notification-title">{notification.title}</div>
        <div className="notification-message">{notification.message}</div>
      </div>
      <button className="notification-close" onClick={handleClose}>
        ✕
      </button>
    </div>
  );
};

interface NotificationContainerProps {
  notifications: NotificationData[];
  onClose: (id: string) => void;
}

export const NotificationContainer: React.FC<NotificationContainerProps> = ({ 
  notifications, 
  onClose 
}) => {
  return (
    <div className="notification-container">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          notification={notification}
          onClose={onClose}
        />
      ))}
    </div>
  );
};