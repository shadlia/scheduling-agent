import { useState, useEffect, useRef } from 'react';
import { apiService } from './apiService';
import { audioService } from './audioService';

/**
 * Custom Hook: Handle complex voice assistant state
 */
export const useVoiceAssistant = (userToken = null, geminiApiKey = null) => {
  const [messages, setMessages] = useState([]);
  const [state, setState] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | thinking | speaking | listening
  const [error, setError] = useState(null);
  const hasInited = useRef(false);
  
  // Track state in a ref to avoid stale closures in audio callbacks
  const stateRef = useRef(state);
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  // Initialize conversation
  const init = async () => {
    if (hasInited.current) return;
    hasInited.current = true;
    
    try {
      setStatus('thinking');
      const data = await apiService.startConversation(geminiApiKey);
      setMessages([{ role: 'assistant', content: data.response }]);
      setState(data.state);
      
      // Speak the greeting
      setStatus('speaking');
      audioService.speak(data.response, () => {
        startListening();
      });
    } catch (err) {
      console.error('Init error:', err);
      setError('Could not connect to backend');
      setStatus('idle');
    }
  };

  // Core logic to send message to backend and handle response
  const handleMessage = async (text, currentState) => {
    try {
      setStatus('thinking');
      // Always use the freshest state available to avoid wiping the backend's memory
      const activeState = currentState || stateRef.current;
      const data = await apiService.sendMessage(text, activeState, userToken, geminiApiKey);
      
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      setState(data.state);

      // Speak response
      setStatus('speaking');
      audioService.speak(data.response, () => {
         // Auto-resume listening only if we are still effectively in "voice mode"
         // and the task isn't complete. 
         if (data.state?.current_step !== 'done' && data.state?.current_step !== 'welcome') {
            startListening();
         } else {
            setStatus('idle');
         }
      });
      return data;
    } catch (err) {
      console.error('Message error:', err);
      setError('Message failed to send. Is the backend running?');
      setStatus('idle');
      throw err;
    }
  };

  const startListening = () => {
    setStatus('listening');
    audioService.listen(
      async (transcript) => {
        if (!transcript) return;
        setMessages(prev => [...prev, { role: 'human', content: transcript }]);
        await handleMessage(transcript);
      },
      (err) => {
        setError(`Speech error: ${err}`);
        setStatus('idle');
      }
    );
  };

  const sendTextMessage = async (text) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { role: 'human', content: text }]);
    await handleMessage(text);
  };

  const toggleVoice = () => {
    if (status === 'listening') {
      audioService.stopListening();
      setStatus('idle');
    } else {
      if (!stateRef.current) {
        init();
      } else {
        startListening();
      }
    }
  };

  return {
    messages,
    state,
    status,
    error,
    toggleVoice,
    sendTextMessage,
    init,
    setMessages,
    setState
  };
};
