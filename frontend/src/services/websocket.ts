import { SimulationState } from '../types';

export class SimulationWebSocket {
  private socket: WebSocket | null = null;
  private onStateUpdate: (state: SimulationState) => void;
  private reconnectInterval: any = null;

  constructor(onStateUpdate: (state: SimulationState) => void) {
    this.onStateUpdate = onStateUpdate;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('Connected to live simulation WebSocket stream');
      if (this.reconnectInterval) {
        clearInterval(this.reconnectInterval);
        this.reconnectInterval = null;
      }
    };

    this.socket.onmessage = (event) => {
      try {
        const data: SimulationState = JSON.parse(event.data);
        this.onStateUpdate(data);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    this.socket.onerror = (error) => {
      console.warn('WebSocket connection error:', error);
    };

    this.socket.onclose = () => {
      console.warn('WebSocket connection closed. Reconnecting in 3s...');
      if (!this.reconnectInterval) {
        this.reconnectInterval = setInterval(() => this.connect(), 3000);
      }
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
    }
    if (this.reconnectInterval) {
      clearInterval(this.reconnectInterval);
    }
  }
}
