/**
 * Audio Service - Managed Web Speech API (STT & TTS)
 */

export class AudioService {
  constructor() {
    this.recognition = null;
    this.synth = window.speechSynthesis;
    this.isListening = false;
    
    // Initialize Speech Recognition if supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true; // Use continuous with manual stop for better control
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';
    }

    this.silenceTimer = null;
    // Resilience: ensure voices are loaded
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = () => this.synth.getVoices();
    }
  }

  // Text to Speech
  speak(text, onEnd) {
    this.synth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    const voices = this.synth.getVoices();
    const premiumVoice = voices.find(v => (v.name.includes('Google') || v.name.includes('Microsoft' )) && v.lang.startsWith('en'));
    if (premiumVoice) utterance.voice = premiumVoice;

    if (onEnd) utterance.onend = onEnd;
    this.synth.speak(utterance);
  }

  // Speech to Text
  listen(onResult, onError) {
    if (!this.recognition) {
      console.error('Speech recognition not supported');
      return;
    }

    let finalTranscript = '';

    this.recognition.onresult = (event) => {
      clearTimeout(this.silenceTimer);
      
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const currentSpeech = (finalTranscript + interimTranscript).trim();
      
      // Start/Reset watchdog timer if we have some speech
      if (currentSpeech) {
        this.silenceTimer = setTimeout(() => {
          if (this.isListening) {
            onResult(currentSpeech);
            this.stopListening();
          }
        }, 1500); // 1.5s Threshold
      }
    };

    this.recognition.onerror = (event) => {
      clearTimeout(this.silenceTimer);
      console.error('Speech recognition error:', event.error);
      if (onError) onError(event.error);
    };

    this.recognition.onend = () => {
      clearTimeout(this.silenceTimer);
      this.isListening = false;
    };

    try {
      this.recognition.start();
      this.isListening = true;
    } catch (e) {
      console.error('Start listening error:', e);
    }
  }

  stopListening() {
    clearTimeout(this.silenceTimer);
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }

  cancelAll() {
    this.synth.cancel();
    this.stopListening();
  }
}

export const audioService = new AudioService();
