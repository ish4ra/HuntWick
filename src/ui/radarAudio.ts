export type Cue = 'scan' | 'verified' | 'provider' | 'possible' | 'conflict'

let audio: AudioContext | undefined
let lastDetection = -Infinity
const voices = new Set<AudioBufferSourceNode>()

export async function armRadar(): Promise<boolean> {
  try {
    audio ??= new AudioContext()
    if (audio.state !== 'running') await audio.resume()
    return audio.state === 'running'
  } catch { return false }
}

// Original two-part chirps. Render the same PCM for browser playback and owner previews.
export function synthesize(cue: Cue, rate: number): Float32Array {
  const score = {
    scan: [640, 440, .065], verified: [790, 1220, .32], provider: [590, 850, .27],
    possible: [710, 510, .25], conflict: [470, 330, .21],
  }[cue]
  const [start, end, length] = score
  const data = new Float32Array(Math.ceil(length * rate))
  let phase = 0
  for (let i = 0; i < data.length; i++) {
    const t = i/rate, u = t/length
    phase += 2*Math.PI*(end+(start-end)*Math.exp(-5*u))/rate
    const onset = Math.min(1,t/.008)
    const echo = cue === 'scan' ? 0 : Math.max(0, 1-Math.abs(u-.49)/.16)*.38
    const envelope = onset*(Math.exp(-6*u)+echo)*(1-u)
    data[i] = (.74*Math.sin(phase)+.19*Math.sin(phase*2.003)+.07*Math.sin(phase*3))*envelope
  }
  return data
}

export function playCue(cue: Cue, volume: number, preview=false) {
  if (!audio || audio.state !== 'running' || volume <= 0) return
  if (cue !== 'scan' && !preview && performance.now()-lastDetection < 400) return
  if (cue !== 'scan') lastDetection = performance.now()
  if (voices.size >= 2) return
  const samples = synthesize(cue, audio.sampleRate)
  const buffer = audio.createBuffer(1,samples.length,audio.sampleRate)
  buffer.getChannelData(0).set(samples)
  const voice=audio.createBufferSource(), gain=audio.createGain()
  voice.buffer=buffer
  gain.gain.value=volume*(cue==='scan'?.0006:.002)
  voice.connect(gain).connect(audio.destination)
  voices.add(voice)
  voice.onended=()=>{voices.delete(voice);voice.disconnect();gain.disconnect()}
  voice.start()
}

export function stopRadar() {
  for (const voice of voices) voice.stop()
  voices.clear()
}
