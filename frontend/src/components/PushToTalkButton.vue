<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSessionStore } from '@/stores/session'
import { JarvisSocket } from '@/services/socket'
import { AudioCapture } from '@/audio/capture'
import { AudioPlayer } from '@/audio/player'

const store = useSessionStore()
const player = new AudioPlayer()
const socket = new JarvisSocket(
  (data) => player.playPcm16(data),
  () => player.stop(),
)
const capture = new AudioCapture()
const micEnabled = ref(false)
const micError = ref('')
const mode = ref<'idle' | 'listening' | 'thinking' | 'speaking'>('idle')

onMounted(() => {
  socket.connect()
})

const enableMic = async () => {
  micError.value = ''
  try {
    await player.resume()
    await capture.start((frame) => socket.sendAudio(frame))
    micEnabled.value = true
    mode.value = 'listening'
  } catch (e: any) {
    micError.value = e?.message || 'Failed to access microphone'
    console.error(e)
  }
}

const bargeIn = () => {
  socket.interrupt()
  player.stop()
}
</script>

<template>
  <div class="flex flex-col items-center gap-6">
    <div class="text-center">
      <p class="text-sm text-slate-400">State</p>
      <p class="text-2xl font-semibold capitalize">{{ store.state }}</p>
    </div>

    <div v-if="!micEnabled" class="flex flex-col items-center gap-3">
      <button
        class="rounded-full px-8 py-8 text-lg font-semibold shadow-lg transition bg-cyan-400 text-slate-950 hover:bg-cyan-300"
        @click="enableMic"
      >
        Enable Microphone
      </button>
      <p class="text-sm text-slate-400">Say "Hey Jarvis" or just speak</p>
      <p v-if="micError" class="text-sm text-red-400">{{ micError }}</p>
    </div>

    <template v-else>
      <div class="relative">
        <div
          class="rounded-full transition-all duration-300 animate-pulse"
          :class="{
            'w-32 h-32 bg-slate-600': store.state === 'idle',
            'w-36 h-36 bg-cyan-400 shadow-[0_0_80px_rgba(34,211,238,0.7)]': store.state === 'listening',
            'w-36 h-36 bg-amber-400 shadow-[0_0_80px_rgba(251,191,36,0.7)] animate-bounce': store.state === 'thinking',
            'w-40 h-40 bg-emerald-400 shadow-[0_0_100px_rgba(52,211,153,0.8)]': store.state === 'speaking',
          }"
        ></div>
        <div class="absolute inset-0 flex items-center justify-center">
          <span class="text-slate-950 font-bold text-lg">J</span>
        </div>
      </div>

      <button v-if="store.speaking" class="text-sm text-slate-300" @click="bargeIn">Interrupt</button>

      <div class="w-full max-w-md space-y-2 text-sm">
        <div>
          <p class="text-slate-400">You</p>
          <p>{{ store.userTranscript || '—' }}</p>
        </div>
        <div>
          <p class="text-slate-400">Jarvis</p>
          <p>{{ store.assistantTranscript || '—' }}</p>
        </div>
      </div>

      <details class="w-full max-w-md">
        <summary class="cursor-pointer text-slate-400">Latency</summary>
        <ul class="mt-2 space-y-1 text-xs">
          <li v-for="(value, key) in store.lastLatency" :key="key" class="flex justify-between">
            <span>{{ key }}</span>
            <span>{{ value.toFixed(1) }} ms</span>
          </li>
        </ul>
      </details>

      <p v-if="store.error" class="text-sm text-red-400">{{ store.error }}</p>
    </template>
  </div>
</template>
