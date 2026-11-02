export interface ReadyEvent {
  type: 'ready'
  input_sample_rate: number
  output_sample_rate: number
}

export interface StateEvent {
  type: 'state'
  state: 'idle' | 'listening' | 'thinking' | 'speaking'
}

export interface UserTranscriptEvent {
  type: 'user_transcript'
  text: string
  final: boolean
}

export interface AssistantTranscriptEvent {
  type: 'assistant_transcript'
  text: string
  final: boolean
}

export interface LatencyEvent {
  type: 'latency'
  turn: number
  marks: Record<string, number>
}

export interface InterruptedEvent {
  type: 'interrupted'
}

export interface ErrorEvent {
  type: 'error'
  message: string
}

export type ServerEvent =
  | ReadyEvent
  | StateEvent
  | UserTranscriptEvent
  | AssistantTranscriptEvent
  | LatencyEvent
  | InterruptedEvent
  | ErrorEvent
