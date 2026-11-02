export class AudioPlayer {
  private ctx: AudioContext
  private queue: Float32Array[] = []
  private playing = false
  private nextTime = 0

  constructor() {
    this.ctx = new AudioContext({ sampleRate: 24000 })
  }

  async resume() {
    await this.ctx.resume()
  }

  playPcm16(buffer: ArrayBuffer) {
    const view = new DataView(buffer)
    const samples = new Float32Array(buffer.byteLength / 2)
    for (let i = 0; i < samples.length; i++) {
      const s = view.getInt16(i * 2, true)
      samples[i] = s < 0 ? s / 0x8000 : s / 0x7fff
    }
    this.queue.push(samples)
    if (!this.playing) {
      this.play()
    }
  }

  private play() {
    this.playing = true
    while (this.queue.length > 0) {
      const samples = this.queue.shift()!
      const buffer = this.ctx.createBuffer(1, samples.length, this.ctx.sampleRate)
      buffer.copyToChannel(samples, 0)
      const source = this.ctx.createBufferSource()
      source.buffer = buffer
      source.connect(this.ctx.destination)
      const now = this.ctx.currentTime
      const start = Math.max(now, this.nextTime)
      source.start(start)
      this.nextTime = start + buffer.duration
    }
    this.playing = false
    this.nextTime = Math.max(this.ctx.currentTime, this.nextTime)
  }

  stop() {
    this.queue = []
    this.playing = false
    this.nextTime = this.ctx.currentTime
  }
}
