import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, MicOff, Send, Calendar, User, Clock, 
  CheckCircle, Loader2, AlertCircle, MessageSquare, 
  Settings, LayoutDashboard, History, LogOut, LogIn,
  ChevronLeft, ChevronRight, RefreshCw, X, MapPin, AlignLeft
} from 'lucide-react';
import { useGoogleLogin } from '@react-oauth/google';
import { useVoiceAssistant } from './services/useVoiceAssistant';
import { apiService } from './services/apiService';
import './index.css';

const App = () => {
  // Authentication State
  const [userToken, setUserToken] = useState(() => {
    const saved = localStorage.getItem('google_token');
    return saved ? JSON.parse(saved) : null;
  });

  // Gemini API Key State
  const [userGeminiKey, setUserGeminiKey] = useState(() => localStorage.getItem('gemini_api_key') || '');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const { 
    messages, state, status, error: voiceError, 
    toggleVoice, sendTextMessage, init, setMessages, setState 
  } = useVoiceAssistant(userToken, userGeminiKey);

  const [textInput, setTextInput] = useState('');
  const [currentView, setCurrentView] = useState('overview'); // 'overview' | 'schedule'
  const [viewDate, setViewDate] = useState(new Date());
  const [viewType, setViewType] = useState('month'); // 'month' | 'week' | 'day'
  const [selectedEvent, setSelectedEvent] = useState(null);
  
  const [isStarted, setIsStarted] = useState(false);
  
  const [events, setEvents] = useState([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [apiError, setApiError] = useState(null);
  const chatEndRef = useRef(null);

  // Auto-scroll chat
  const scrollContainerRef = useRef(null);
  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, status]);


  // Handle Google Login
  const login = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      setLoadingEvents(true);
      try {
        const data = await apiService.googleAuth(tokenResponse.code);
        setUserToken(data);
        localStorage.setItem('google_token', JSON.stringify(data));
        setApiError(null);
        setCurrentView('schedule');
      } catch (err) {
        console.error('Auth exchange error:', err);
        setApiError('Authentication failed. Check backend logs.');
      } finally {
        setLoadingEvents(false);
      }
    },
    onError: (error) => console.error('Login Failed:', error),
    flow: 'auth-code',
    scope: 'https://www.googleapis.com/auth/calendar'
  });

  const logout = () => {
    setUserToken(null);
    localStorage.removeItem('google_token');
    setCurrentView('overview');
    setMessages([]);
    setState(null);
  };

  // Fetch events when switching view or month
  useEffect(() => {
    if (currentView === 'schedule') {
      fetchEvents();
    }
  }, [currentView, userToken, viewDate, viewType]);

  const fetchEvents = async () => {
    setLoadingEvents(true);
    setApiError(null);
    try {
      let start, end;
      if (viewType === 'month') {
        start = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1);
        end = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0);
      } else if (viewType === 'week') {
        start = new Date(viewDate);
        start.setDate(viewDate.getDate() - viewDate.getDay());
        end = new Date(start);
        end.setDate(start.getDate() + 6);
      } else {
        start = new Date(viewDate);
        end = new Date(viewDate);
      }
      
      start.setHours(0,0,0,0);
      end.setHours(23,59,59,999);

      const data = await apiService.getCalendarEvents(userToken, start.toISOString(), end.toISOString());
      setEvents(data);
    } catch (err) {
      console.error('Error fetching events:', err);
      setApiError('Could not fetch calendar events.');
    } finally {
      setLoadingEvents(false);
    }
  };

  const handleSendText = (e) => {
    if (e) e.preventDefault();
    if (textInput.trim()) {
      sendTextMessage(textInput.trim());
      setTextInput('');
    }
  };


  const handleStart = () => {
    if (!userGeminiKey) return;
    setIsStarted(true);
    if (messages.length === 0) {
      init();
    }
  };

  const handleWelcomeKeySave = (key) => {
    setUserGeminiKey(key);
    localStorage.setItem('gemini_api_key', key);
    setIsStarted(true);
  };

  useEffect(() => {
    if (isStarted && userGeminiKey && messages.length === 0) {
      init();
    }
  }, [isStarted, userGeminiKey]);

  const getOrbColor = () => {
    switch (status) {
      case 'listening': return 'var(--accent-secondary)';
      case 'thinking': return 'var(--accent-tertiary)';
      case 'speaking': return 'var(--accent-primary)';
      default: return 'var(--accent-primary)';
    }
  };

  return (
    <div className="app-wrapper">
      {!isStarted && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="welcome-overlay">
          <div className="nebula" />
          <motion.div 
            className="welcome-logo" 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'white', opacity: 0.9 }} />
          </motion.div>
          
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: 'white', opacity: 0.6, fontSize: '0.9rem', letterSpacing: '0.2em', marginBottom: '0.5rem' }}>SMART CALENDAR</div>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 700, marginBottom: '2rem' }}>Welcome to the Future of Scheduling</h1>
          </div>

          {!userGeminiKey ? (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ width: '100%', maxWidth: '400px', display: 'flex', flexDirection: 'column', gap: '1rem' }}
            >
              <div style={{ position: 'relative' }}>
                <input 
                  type="password" 
                  className="command-input" 
                  placeholder="Enter your Gemini API Key..." 
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.target.value.trim()) {
                      handleWelcomeKeySave(e.target.value.trim());
                    }
                  }}
                  autoFocus
                  style={{ width: '100%', textAlign: 'center', background: 'rgba(255,255,255,0.05)', padding: '1.2rem' }}
                />
              </div>
              <p style={{ fontSize: '0.8rem', opacity: 0.4, textAlign: 'center' }}>
                Get your key at <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)' }}>Google AI Studio</a>.
              </p>
              <button 
                className="enter-btn"
                onClick={(e) => {
                  const input = e.currentTarget.parentElement.querySelector('input');
                  if (input.value.trim()) handleWelcomeKeySave(input.value.trim());
                }}
              >
                Start Experience
              </button>
            </motion.div>
          ) : (
            <motion.button 
              className="enter-btn"
              onClick={handleStart}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              Enter Experience
            </motion.button>
          )}
        </motion.div>
      )}

      <div className="nebula" />
      
      <header className="top-bar">
        <div className="user-profile-plate">
          {userToken ? (
            <>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Personal Active</div>
              <button className="auth-btn-premium" onClick={logout} style={{ background: 'rgba(255,255,255,0.1)', boxShadow: 'none' }}>
                <LogOut size={14} />
              </button>
            </>
          ) : (
            <>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Guest Mode</div>
              <button className="auth-btn-premium" onClick={() => login()}>Connect Google</button>
            </>
          )}
        </div>
      </header>

      <aside className="sidebar">
        <div className="sidebar-logo">
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))' }} />
          <span>SMART CALENDAR</span>
        </div>
        <nav className="history-list">
          <SidebarItem icon={<LayoutDashboard size={18} />} label="Overview" active={currentView === 'overview'} onClick={() => setCurrentView('overview')} />
          <SidebarItem icon={<Calendar size={18} />} label="Schedule" active={currentView === 'schedule'} onClick={() => setCurrentView('schedule')} />
          <div style={{ margin: '1rem 0', height: '1px', background: 'rgba(255,255,255,0.05)' }} />
          <SidebarItem icon={<History size={18} />} label="Activity" onClick={() => {}} />
          <div style={{ marginTop: 'auto' }}>
             <SidebarItem 
               icon={<Settings size={18} />} 
               label="Settings" 
               active={isSettingsOpen}
               onClick={() => setIsSettingsOpen(true)} 
             />
          </div>
        </nav>
      </aside>

      <main className="main-canvas">
        {currentView === 'overview' ? (
          <div className="overview-full-container">
            <div className="transcript-overlay" ref={scrollContainerRef}>
              <AnimatePresence>
                {messages.map((msg, i) => (
                  <motion.div 
                    key={i} 
                    initial={{ opacity: 0, y: 10 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    className={`message-row ${msg.role === 'human' ? 'human' : 'ai'}`}
                  >
                    {msg.role === 'assistant' ? (
                      <div className={`avatar-orb ${status}`} style={{ background: `radial-gradient(circle at 30% 30%, ${getOrbColor()}, rgba(0,0,0,0.8))` }} />
                    ) : (
                      <div className="avatar-orb human"><User size={16} /></div>
                    )}
                    <div className={`transcript-msg ${msg.role === 'human' ? 'human' : 'ai'}`}>
                      {msg.content}
                    </div>
                  </motion.div>
                ))}
                
                {status === 'thinking' && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    className="message-row ai"
                  >
                    <div className="avatar-orb thinking" style={{ background: `radial-gradient(circle at 30% 30%, ${getOrbColor()}, rgba(0,0,0,0.8))` }} />
                    <div className="ai-typing">
                      <div className="typing-dot" />
                      <div className="typing-dot" />
                      <div className="typing-dot" />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="command-container">
              <form className="command-bar" onSubmit={handleSendText}>
                <MessageSquare size={18} style={{ opacity: 0.4 }} />
                <input 
                  type="text" 
                  className="command-input" 
                  value={textInput} 
                  onChange={(e) => setTextInput(e.target.value)} 
                  placeholder={!userGeminiKey ? "Configure Gemini API Key to start..." : (status === 'listening' ? "I'm listening..." : "Type a command...") } 
                  disabled={status === 'thinking' || !userGeminiKey} 
                />
                <button 
                  type="button" 
                  className={`voice-suffix-btn ${status === 'listening' ? 'active' : ''}`} 
                  onClick={!userGeminiKey ? () => setIsSettingsOpen(true) : toggleVoice}
                >
                  {status === 'thinking' ? <Loader2 size={20} className="animate-spin" /> : <Mic size={20} />}
                </button>
                <button type="submit" className="voice-suffix-btn" disabled={!textInput.trim() || status === 'thinking' || !userGeminiKey}><Send size={18} /></button>
              </form>
              
              {!userGeminiKey && isStarted && (
                <motion.div 
                   initial={{ opacity: 0, scale: 0.95 }}
                   animate={{ opacity: 1, scale: 1 }}
                   className="context-chip"
                   style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)', color: '#fca5a5', cursor: 'pointer', margin: '0.5rem auto' }}
                   onClick={() => setIsSettingsOpen(true)}
                >
                   <AlertCircle size={14} />
                   <span>API Key Required - Configure in Settings</span>
                </motion.div>
              )}
              <div className="context-chips-panel">
                <AnimatePresence>
                  {state?.name && <ContextChip icon={<User size={12}/>} label={state.name} />}
                  {state?.date_time && <ContextChip icon={<Clock size={12}/>} label={state.date_time} />}
                  {state?.meeting_title && <ContextChip icon={<Calendar size={12}/>} label={state.meeting_title} />}
                </AnimatePresence>
              </div>
            </div>
          </div>
        ) : (
          <CalendarView 
            events={events} 
            loading={loadingEvents} 
            error={apiError} 
            onRefresh={fetchEvents}
            viewDate={viewDate}
            setViewDate={setViewDate}
            viewType={viewType}
            setViewType={setViewType}
            onSelectEvent={setSelectedEvent}
          />
        )}
      </main>

      <AnimatePresence>
        {selectedEvent && (
          <EventDetailsModal 
            event={selectedEvent} 
            onClose={() => setSelectedEvent(null)} 
          />
        )}
        {isSettingsOpen && (
          <SettingsModal 
            userKey={userGeminiKey} 
            onSave={(key) => {
              setUserGeminiKey(key);
              localStorage.setItem('gemini_api_key', key);
              setIsSettingsOpen(false);
            }}
            onClose={() => setIsSettingsOpen(false)} 
          />
        )}
      </AnimatePresence>
    </div>
  );
};

const SidebarItem = ({ icon, label, active, onClick }) => (
  <button className={`sidebar-item ${active ? 'active' : ''}`} onClick={onClick}>{icon}<span>{label}</span></button>
);

const ContextChip = ({ icon, label }) => (
  <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} className="context-chip">{icon}<span>{label}</span></motion.div>
);

const SettingsModal = ({ userKey, onSave, onClose }) => {
  const [tempKey, setTempKey] = useState(userKey);
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div 
        className="modal-content" 
        onClick={e => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
        style={{ maxWidth: '400px' }}
      >
        <button className="modal-close" onClick={onClose}><X size={20} /></button>
        <div className="modal-header">
          <h3 className="modal-title">Settings</h3>
          <p style={{ fontSize: '0.85rem', opacity: 0.6, marginTop: '0.5rem' }}>
            Configure your personal AI preferences.
          </p>
        </div>
        
        <div style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="setting-group">
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 'bold', textTransform: 'uppercase', marginBottom: '0.5rem', opacity: 0.8 }}>
              Gemini API Key
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input 
                type="password" 
                className="command-input" 
                value={tempKey} 
                onChange={(e) => setTempKey(e.target.value)} 
                placeholder="Paste your API key here..." 
                style={{ flex: 1, background: 'rgba(255,255,255,0.05)', borderRadius: '10px', padding: '0.75rem' }}
              />
            </div>
            <p style={{ fontSize: '0.7rem', opacity: 0.4, marginTop: '0.5rem' }}>
              Get one free at <a href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)' }}>Google AI Studio</a>. 
              Leave empty to use the server's default key.
            </p>
          </div>

          <button 
            className="enter-btn" 
            onClick={() => onSave(tempKey)}
            style={{ width: '100%', padding: '0.75rem' }}
          >
            Save Configuration
          </button>
        </div>
      </motion.div>
    </div>
  );
};

const EventDetailsModal = ({ event, onClose }) => {
  const start = new Date(event.start);
  const end = new Date(event.end);
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div 
        className="modal-content" 
        onClick={e => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.9, y: 20 }}
      >
        <button className="modal-close" onClick={onClose}><X size={20} /></button>
        <div className="modal-header">
          <h3 className="modal-title">{event.summary || '(No Title)'}</h3>
          <div className="modal-info-row">
            <Clock className="modal-info-icon" size={16} />
            <span>
              {start.toLocaleDateString('default', { weekday: 'long', month: 'long', day: 'numeric' })}
              <br />
              {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          {event.location && (
            <div className="modal-info-row">
              <MapPin className="modal-info-icon" size={16} />
              <span>{event.location}</span>
            </div>
          )}
        </div>
        
        <div className="modal-description">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--accent-primary)' }}>
            <AlignLeft size={16} />
            <span style={{ fontSize: '0.8rem', fontWeight: 'bold', textTransform: 'uppercase' }}>Description</span>
          </div>
          {event.description || 'No description provided.'}
        </div>
      </motion.div>
    </div>
  );
};

const CalendarView = ({ events, loading, error, onRefresh, viewDate, setViewDate, viewType, setViewType, onSelectEvent }) => {
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const formatHeader = () => {
    if (viewType === 'day') return viewDate.toLocaleDateString('default', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
    if (viewType === 'month') return viewDate.toLocaleString('default', { month: 'long', year: 'numeric' });
    
    const startOfWeek = new Date(viewDate);
    startOfWeek.setDate(viewDate.getDate() - viewDate.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    return `${startOfWeek.toLocaleDateString('default', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('default', { month: 'short', day: 'numeric', year: 'numeric' })}`;
  };

  const navigate = (direction) => {
    const newDate = new Date(viewDate);
    if (viewType === 'month') newDate.setMonth(viewDate.getMonth() + direction);
    else if (viewType === 'week') newDate.setDate(viewDate.getDate() + (direction * 7));
    else newDate.setDate(viewDate.getDate() + direction);
    setViewDate(newDate);
  };

  return (
    <div className="calendar-view">
      <div className="calendar-header">
        <div className="calendar-header-left">
          <h2 className="gradient-text" style={{ fontSize: '1.4rem', minWidth: '220px' }}>{formatHeader()}</h2>
          <div className="view-switcher">
            <button className={`view-btn ${viewType === 'month' ? 'active' : ''}`} onClick={() => setViewType('month')}>Month</button>
            <button className={`view-btn ${viewType === 'week' ? 'active' : ''}`} onClick={() => setViewType('week')}>Week</button>
            <button className={`view-btn ${viewType === 'day' ? 'active' : ''}`} onClick={() => setViewType('day')}>Day</button>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div className="calendar-nav-group">
            <button className="calendar-nav-btn" onClick={() => navigate(-1)}><ChevronLeft size={20} /></button>
            <button className="calendar-nav-btn" onClick={() => setViewDate(new Date())} style={{ fontSize: '0.8rem', padding: '0 0.75rem' }}>Today</button>
            <button className="calendar-nav-btn" onClick={() => navigate(1)}><ChevronRight size={20} /></button>
          </div>
          <button onClick={onRefresh} className="calendar-refresh-btn">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          </button>
        </div>
      </div>
      
      {error && <div style={{ color: '#ff4444', marginBottom: '1rem', fontStyle: 'italic', fontSize: '0.85rem' }}>{error}</div>}

      {viewType === 'month' ? (
        <MonthGrid events={events} viewDate={viewDate} onSelectEvent={onSelectEvent} />
      ) : (
        <HourlyGrid events={events} viewDate={viewDate} viewType={viewType} onSelectEvent={onSelectEvent} />
      )}
    </div>
  );
};

const MonthGrid = ({ events, viewDate, onSelectEvent }) => {
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  
  const cells = [];
  // Correctly handle previous month padding
  for (let i = firstDay - 1; i >= 0; i--) {
    const d = new Date(year, month, -i);
    cells.push({ day: d.getDate(), current: false, date: d });
  }
  
  // Current month days
  for (let i = 1; i <= daysInMonth; i++) {
    cells.push({ day: i, current: true, date: new Date(year, month, i) });
  }
  
  // Ensure we always have 42 cells (6 rows) to prevent cutoffs
  const remaining = 42 - cells.length;
  for (let i = 1; i <= remaining; i++) {
    const d = new Date(year, month + 1, i);
    cells.push({ day: d.getDate(), current: false, date: d });
  }

  const getEvents = (date) => {
    const ds = date.toDateString();
    return events.filter(e => new Date(e.start).toDateString() === ds);
  };

  return (
    <div className="month-grid-container">
      <div className="month-grid-header">
        <div className="time-column-pad" />
        {dayNames.map(d => (
          <div key={d} className="day-column-header">
            <span style={{ fontSize: '0.65rem', opacity: 0.5, fontWeight: '700' }}>{d.toUpperCase()}</span>
          </div>
        ))}
      </div>
      <div className="month-body-grid">
        {cells.map((c, idx) => {
          const evs = c.current ? getEvents(c.date) : [];
          const isToday = c.date.toDateString() === new Date().toDateString();
          return (
            <React.Fragment key={idx}>
              {idx % 7 === 0 && <div className="time-column-pad" />}
              <div className={`month-cell ${c.current ? 'current' : 'other'} ${isToday ? 'today' : ''}`}>
                <span className="day-number" style={{ opacity: c.current ? 1 : 0.3 }}>{c.day}</span>
                <div className="day-events-list">
                  {evs.slice(0, 3).map((e, ei) => (
                    <div key={ei} className="event-tag" onClick={(ev) => { ev.stopPropagation(); onSelectEvent(e); }}>{e.summary}</div>
                  ))}
                  {evs.length > 3 && (
                    <div className="event-more">+{evs.length - 3} more</div>
                  )}
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

const HourlyGrid = ({ events, viewDate, viewType, onSelectEvent }) => {
  // 🧪 MOCK DATA FOR LAYOUT VERIFICATION
  const today = new Date();
  const mockEvents = [
    {
      id: 'mock-1',
      summary: 'Project Sync (Live Sync Test)',
      start: new Date(today.getFullYear(), today.getMonth(), today.getDate(), 10, 0).toISOString(),
      end: new Date(today.getFullYear(), today.getMonth(), today.getDate(), 11, 30).toISOString(),
    },
    {
      id: 'mock-2',
      summary: 'Frontend Alignment Fix',
      start: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1, 14, 0).toISOString(),
      end: new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1, 16, 0).toISOString(),
    }
  ];

  const activeEvents = events.length > 0 ? events : mockEvents;
  const hours = Array.from({ length: 24 }, (_, i) => i);
  const days = viewType === 'day' ? [viewDate] : Array.from({ length: 7 }, (_, i) => {
    const d = new Date(viewDate);
    d.setDate(viewDate.getDate() - viewDate.getDay() + i);
    return d;
  });

  const getEventsForDay = (date) => {
    const ds = date.toDateString();
    return activeEvents.filter(e => new Date(e.start).toDateString() === ds);
  };

  const formatHour = (h) => h === 0 ? '12 AM' : h < 12 ? `${h} AM` : h === 12 ? '12 PM' : `${h - 12} PM`;

  return (
    <div className="hourly-grid-container" style={{ '--cols': days.length }}>
      {/* 🏔️ Header Row */}
      <div className="hourly-grid-header-row">
        <div className="time-column-header" />
        {days.map((d, di) => (
          <div key={di} className="day-column-header">
            <span style={{ fontSize: '0.6rem', opacity: 0.5 }}>{d.toLocaleDateString('default', { weekday: 'short' })}</span>
            <span style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>{d.getDate()}</span>
          </div>
        ))}
      </div>

      {/* 🧱 Grid Rows (Aligned by CSS Grid) */}
      <div style={{ position: 'relative' }}>
        {hours.map(h => (
          <div key={h} className="hourly-row">
            <div className="time-cell">{formatHour(h)}</div>
            {days.map((_, di) => <div key={di} className="hour-slot-cell" />)}
          </div>
        ))}

        {/* 🎭 Events Overlay (Matches the Grid perfectly) */}
        <div className="grid-events-layer">
            {days.map((d, di) => (
                <div key={di} className="col-events-container">
                    {getEventsForDay(d).map((e, ei) => {
                        const start = new Date(e.start);
                        const end = new Date(e.end);
                        const startPct = (start.getHours() * 60 + start.getMinutes()) / 1440;
                        const durationPct = ((end - start) / (1000 * 60 * 60 * 24));
                        const totalHeight = 80 * 24;
                        
                        return (
                            <motion.div
                                key={ei}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="event-block"
                                style={{ 
                                    top: `${startPct * totalHeight}px`, 
                                    height: `${durationPct * totalHeight}px` 
                                }}
                                onClick={() => onSelectEvent(e)}
                            >
                                <div style={{ fontWeight: 'bold' }}>{e.summary}</div>
                                <div style={{ fontSize: '0.65rem', opacity: 0.8 }}>
                                    {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default App;
