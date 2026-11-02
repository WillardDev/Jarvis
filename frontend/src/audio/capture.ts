const RESAMPLE_RATIO = 3 // 48 kHz -> 16 kHz

class Resampler {
  private ratio: number
  constructor(from: number, to: number) {
    this.ratio = from / to
  }

  resample(input: Float32Array): Int16Array {
    const outputLength = Math.floor(input.length / this.ratio)
    const output = new Int16Array(outputLength)
    let outputIndex = 0
    let inputIndex = 0
    while (inputIndex < input.length - this.ratio) {
      const i0 = Math.floor(inputIndex)
      const i1 = i0 + 1
      const t = inputIndex - i0
      const sample0 = input[i0]
      const sample1 = i1 < input.length ? input[i1] : sample0
      const interpolated = sample0 * (1 - t) + sample1 * t
      const clamped = Math.max(-1, Math.min(1, interpolated))
      output[outputIndex++] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff
      inputIndex += this.ratio
    }
    return output
  }
}

class InputHandler {
  private ctx: AudioContext
  private processor: ScriptProcessorNode | null = null
  private source: MediaStreamAudioSourceNode | null = null
  private resampler = new Resampler(48000, 16000)
  private onFrame: (data: ArrayBuffer) => void

  constructor(ctx: AudioContext, onFrame: (data: ArrayBuffer) => void) {
    this.ctx = ctx
    this.onFrame = onFrame
  }

  async start(stream: MediaStream) {
    this.source = this.ctx.createMediaStreamSource(stream)
    this.processor = this.ctx.createScriptProcessor(4096, 1, 1)
    this.processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0)
      const resampled = this.resampler.resample(input)
      this.onFrame(resampled.buffer)
    }
    this.source.connect(this.processor)
    this.processor.connect(this.ctx.destination)
  }

  stop() {
    this.processor?.disconnect()
    this.source?.disconnect()
    this.processor = null
    this.source = null
  }
}

export class AudioCapture {
  private ctx: AudioContext
  private handler: InputHandler | null = null
  private stream: MediaStream | null = null

  constructor() {
    this.ctx = new AudioContext({ sampleRate: 48000 })
  }

  async start(onFrame: (data: ArrayBuffer) => void) {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    this.handler = new InputHandler(this.ctx, onFrame)
    await this.ctx.resume()
    await this.handler.start(this.stream)
  }

  stop() {
    this.handler?.stop()
    this.stream?.getTracks().forEach((t) => t.stop())
    this.stream = null
  }
}
