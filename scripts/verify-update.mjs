// Verify Tauri's prehashed minisign package and signed version with Node's native Ed25519.
import {createHash, createPublicKey, verify} from 'node:crypto'
import {readFileSync} from 'node:fs'
import {pathToFileURL} from 'node:url'

export function verifyUpdate(data, encodedKey, encodedSignature, version) {
  const lines = text => Buffer.from(text.trim(), 'base64').toString('utf8').trim().split(/\r?\n/)
  const key = Buffer.from(lines(encodedKey)[1], 'base64')
  const [, signature, comment, globalSignature] = lines(encodedSignature)
  const sig = Buffer.from(signature, 'base64')
  if (key.length !== 42 || sig.length !== 74 || sig.subarray(0,2).toString() !== 'ED' ||
      !sig.subarray(2,10).equals(key.subarray(2,10)) || !comment.startsWith('trusted comment: ')) throw Error('Invalid signing identity')
  const pk = createPublicKey({key:Buffer.concat([Buffer.from('302a300506032b6570032100','hex'),key.subarray(10)]),format:'der',type:'spki'})
  const trusted = comment.slice('trusted comment: '.length)
  if (!verify(null,createHash('blake2b512').update(data).digest(),pk,sig.subarray(10)) ||
      !verify(null,Buffer.concat([sig.subarray(10),Buffer.from(trusted)]),pk,Buffer.from(globalSignature,'base64')) ||
      !trusted.split(/\s+/).includes('version:'+version)) throw Error('Invalid artifact signature or version binding')
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [, , path, version] = process.argv
  verifyUpdate(readFileSync(path),process.env.HUNTWICK_SIGNING_TEST_PUBLIC_KEY,readFileSync(path+'.sig','utf8'),version)
}
