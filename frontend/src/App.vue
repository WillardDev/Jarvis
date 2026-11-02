<script setup lang="ts">
import PushToTalkButton from './components/PushToTalkButton.vue'
</script>

<template>
  <main class="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-8 px-6">
    <header class="text-center">
      <h1 class="text-4xl font-semibold">Jarvis</h1>
      <p class="text-slate-400">Always listening. Say "Hey Jarvis" or speak naturally.</p>
    </header>
    <PushToTalkButton />
  </main>
</template>


