import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
});

export const apiService = {
  startConversation: async (geminiApiKey = null) => {
    const response = await api.post('/start', { gemini_api_key: geminiApiKey });
    return response.data;
  },

  sendMessage: async (message, state, userToken = null, geminiApiKey = null) => {
    const response = await api.post('/chat', {
      message,
      conversation_state: state,
      user_token: userToken,
      gemini_api_key: geminiApiKey,
    });
    return response.data;
  },

  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  getCalendarEvents: async (userToken = null, timeMin = null, timeMax = null) => {
    const response = await api.get('/calendar/events', {
      params: { 
        token: userToken ? JSON.stringify(userToken) : null,
        time_min: timeMin,
        time_max: timeMax
      }
    });
    return response.data;
  },

  googleAuth: async (code) => {
    const response = await api.post('/auth/google', { code });
    return response.data;
  },
};
