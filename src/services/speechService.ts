import { Capacitor } from '@capacitor/core';
import { SpeechRecognition } from '@capacitor-community/speech-recognition';
import { TextToSpeech } from '@capacitor-community/text-to-speech';

export type SpeechRecognitionCallback = (transcript: string) => void;
export type SpeechErrorCallback = (error: string) => void;

class SpeechService {
  private isNative = Capacitor.isNativePlatform();
  private webRecognition: any = null;
  private onResultCallback: SpeechRecognitionCallback | null = null;
  private onErrorCallback: SpeechErrorCallback | null = null;
  private isListening = false;

  constructor() {
    if (!this.isNative) {
      this.initWebSpeechRecognition();
    }
  }

  private initWebSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognitionAPI = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      this.webRecognition = new SpeechRecognitionAPI();
      this.webRecognition.continuous = false;
      this.webRecognition.interimResults = false;

      this.webRecognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (this.onResultCallback) {
          this.onResultCallback(transcript);
        }
      };

      this.webRecognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        if (this.onErrorCallback) {
          this.onErrorCallback(event.error);
        }
      };

      this.webRecognition.onend = () => {
        this.isListening = false;
      };
    }
  }

  async requestPermissions(): Promise<boolean> {
    if (this.isNative) {
      try {
        const result = await SpeechRecognition.requestPermissions();
        return result.speechRecognition === 'granted';
      } catch (error) {
        console.error('Error requesting permissions:', error);
        return false;
      }
    }
    // Web handles permissions automatically when starting recognition
    return true;
  }

  async checkPermissions(): Promise<boolean> {
    if (this.isNative) {
      try {
        const result = await SpeechRecognition.checkPermissions();
        return result.speechRecognition === 'granted';
      } catch (error) {
        console.error('Error checking permissions:', error);
        return false;
      }
    }
    return true;
  }

  isSupported(): boolean {
    if (this.isNative) {
      return true; // Native plugins are always available once installed
    }
    return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
  }

  setLanguage(languageCode: string) {
    if (!this.isNative && this.webRecognition) {
      this.webRecognition.lang = languageCode;
    }
  }

  onResult(callback: SpeechRecognitionCallback) {
    this.onResultCallback = callback;
  }

  onError(callback: SpeechErrorCallback) {
    this.onErrorCallback = callback;
  }

  async startListening(languageCode: string): Promise<void> {
    if (this.isListening) return;

    if (this.isNative) {
      try {
        await SpeechRecognition.start({
          language: languageCode,
          maxResults: 1,
          popup: false,
          partialResults: false,
        });

        this.isListening = true;

        // Set up listener for results
        SpeechRecognition.addListener('partialResults', (data: any) => {
          if (data.matches && data.matches.length > 0 && this.onResultCallback) {
            this.onResultCallback(data.matches[0]);
          }
        });
      } catch (error: any) {
        console.error('Native speech recognition error:', error);
        if (this.onErrorCallback) {
          this.onErrorCallback(error.message || 'Speech recognition failed');
        }
        throw error;
      }
    } else {
      if (!this.webRecognition) {
        throw new Error('Speech recognition not supported');
      }
      this.webRecognition.lang = languageCode;
      this.webRecognition.start();
      this.isListening = true;
    }
  }

  async stopListening(): Promise<void> {
    if (!this.isListening) return;

    if (this.isNative) {
      try {
        await SpeechRecognition.stop();
        await SpeechRecognition.removeAllListeners();
      } catch (error) {
        console.error('Error stopping native speech recognition:', error);
      }
    } else {
      if (this.webRecognition) {
        this.webRecognition.stop();
      }
    }
    this.isListening = false;
  }

  getIsListening(): boolean {
    return this.isListening;
  }
}

class TTSService {
  private isNative = Capacitor.isNativePlatform();

  async speak(text: string, languageCode: string): Promise<void> {
    if (this.isNative) {
      try {
        await TextToSpeech.speak({
          text,
          lang: languageCode,
          rate: 0.9,
          pitch: 1.0,
        });
      } catch (error) {
        console.error('Native TTS error:', error);
        throw error;
      }
    } else {
      return this.browserSpeak(text, languageCode);
    }
  }

  private browserSpeak(text: string, languageCode: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = languageCode;
      utterance.rate = 0.9;
      utterance.pitch = 1;

      utterance.onend = () => resolve();
      utterance.onerror = (event) => reject(new Error(event.error));

      window.speechSynthesis.speak(utterance);
    });
  }

  async stop(): Promise<void> {
    if (this.isNative) {
      try {
        await TextToSpeech.stop();
      } catch (error) {
        console.error('Error stopping native TTS:', error);
      }
    } else {
      window.speechSynthesis.cancel();
    }
  }

  isSupported(): boolean {
    if (this.isNative) {
      return true;
    }
    return 'speechSynthesis' in window;
  }
}

// Export singleton instances
export const speechService = new SpeechService();
export const ttsService = new TTSService();

// Export utility to check if running on native platform
export const isNativePlatform = () => Capacitor.isNativePlatform();
