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

onMounted(async () => {
  socket.connect()
  await player.resume()
  await capture.start((frame) => socket.sendAudio(frame))
})

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

    <div
      class="rounded-full px-16 py-16 transition-all duration-300"
      :class="{
        'bg-cyan-400 shadow-[0_0_60px_rgba(34,211,238,0.6)]': store.state === 'listening',
        'bg-amber-400 shadow-[0_0_60px_rgba(251,191,36,0.6)]': store.state === 'thinking',
        'bg-emerald-400 shadow-[0_0_60px_rgba(52,211,153,0.6)]': store.state === 'speaking',
        'bg-slate-600': store.state === 'idle',
      }"
    ></div>

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
  </div>
</template>
