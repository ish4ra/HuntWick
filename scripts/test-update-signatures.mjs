import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {verifyUpdate} from './verify-update.mjs'
const file = name => readFileSync(new URL('./fixtures/update/'+name,import.meta.url),'utf8')
const key=file('key.pub'), sig=file('sample.sig'), data=file('sample'), version='0.1.0-rc.2'
test('official Tauri CLI signature and version binding',()=>verifyUpdate(data,key,sig,version))
test('tampered bytes are rejected',()=>assert.throws(()=>verifyUpdate(data+'x',key,sig,version)))
test('relabelled old artifact is rejected',()=>assert.throws(()=>verifyUpdate(data,key,sig,'1.0.0')))
test('invalid signature is rejected',()=>assert.throws(()=>verifyUpdate(data,key,'invalid',version)))
