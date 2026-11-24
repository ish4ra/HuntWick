let audio: AudioContext | undefined
let lastPing = -Infinity

export function armRadar() {
  try { audio ??= new AudioContext(); void audio.resume().catch(() => {}) } catch { /* Audio is optional. */ }
}
export function pingRadar(possible: boolean, volume: number) {
  if (!audio || audio.state !== 'running' || performance.now()-lastPing < 400 || volume <= 0) return
  lastPing = performance.now()
  const tone=audio.createOscillator(), gain=audio.createGain(), start=audio.currentTime
  tone.frequency.setValueAtTime(possible ? 560 : 940,start)
  tone.frequency.exponentialRampToValueAtTime(possible ? 410 : 740,start+.22)
  gain.gain.setValueAtTime(.0001,start)
  gain.gain.exponentialRampToValueAtTime(Math.max(.0002,volume*.0008),start+.012)
  gain.gain.exponentialRampToValueAtTime(.0001,start+.25)
  tone.connect(gain).connect(audio.destination)
  tone.onended=()=>{tone.disconnect();gain.disconnect()}
  tone.start(start);tone.stop(start+.26)
}
