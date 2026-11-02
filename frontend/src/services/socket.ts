import { useSessionStore } from '@/stores/session'
import type { ServerEvent } from '@/types/protocol'

export class JarvisSocket {
  private ws: WebSocket | null = null
  private store = useSessionStore()
  private onAudio: ((data: ArrayBuffer) => void) | null = null
  private onInterrupt: (() => void) | null = null

  constructor(onAudio: (data: ArrayBuffer) => void, onInterrupt: () => void) {
    this.onAudio = onAudio
    this.onInterrupt = onInterrupt
  }

  connect() {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${location.host}/ws`
    this.ws = new WebSocket(url)
    this.ws.binaryType = 'arraybuffer'
    this.ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        this.onAudio?.(event.data)
        return
      }
      try {
        const parsed = JSON.parse(event.data) as ServerEvent
        this.store.onEvent(parsed)
        if (parsed.type === 'interrupted') {
          this.onInterrupt?.()
        }
      } catch {
        // ignore
      }
    }
    this.ws.onclose = () => {
      this.store.connected = false
    }
  }

  startRecording() {
    this.ws?.send(JSON.stringify({ type: 'record_start' }))
  }

  sendAudio(data: ArrayBuffer) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data)
    }
  }

  stopRecording() {
    this.ws?.send(JSON.stringify({ type: 'record_stop' }))
  }

  interrupt() {
    this.ws?.send(JSON.stringify({ type: 'interrupt' }))
  }
}
