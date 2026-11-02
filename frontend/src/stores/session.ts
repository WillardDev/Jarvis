import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ServerEvent } from '@/types/protocol'

export type State = 'idle' | 'listening' | 'thinking' | 'speaking'

export const useSessionStore = defineStore('session', () => {
  const connected = ref(false)
  const state = ref<State>('idle')
  const inputSampleRate = ref(16000)
  const outputSampleRate = ref(24000)
  const userTranscript = ref('')
  const assistantTranscript = ref('')
  const lastLatency = ref<Record<string, number> | null>(null)
  const error = ref<string | null>(null)

  const canListen = computed(() => connected.value && (state.value === 'idle' || state.value === 'speaking'))
  const speaking = computed(() => state.value === 'speaking')

  function onEvent(event: ServerEvent) {
    if (event.type === 'ready') {
      connected.value = true
      inputSampleRate.value = event.input_sample_rate
      outputSampleRate.value = event.output_sample_rate
      return
    }
    if (event.type === 'state') {
      state.value = event.state
      return
    }
    if (event.type === 'user_transcript') {
      userTranscript.value = event.text
      return
    }
    if (event.type === 'assistant_transcript') {
      if (event.final) {
        assistantTranscript.value = assistantTranscript.value + event.text
      } else {
        assistantTranscript.value = assistantTranscript.value + event.text
      }
      return
    }
    if (event.type === 'latency') {
      lastLatency.value = event.marks
      return
    }
    if (event.type === 'interrupted') {
      return
    }
    if (event.type === 'error') {
      error.value = event.message
    }
  }

  return {
    connected,
    state,
    inputSampleRate,
    outputSampleRate,
    userTranscript,
    assistantTranscript,
    lastLatency,
    error,
    canListen,
    speaking,
    onEvent,
  }
})
