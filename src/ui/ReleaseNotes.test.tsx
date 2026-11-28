import { renderToStaticMarkup } from 'react-dom/server'
import { expect, test } from 'vitest'
import notes from '../../scripts/fixtures/update/rc6-published-notes.md?raw'
import { ReleaseNotes } from './ReleaseNotes'

test('renders the published RC.6 version, headings and bullets as individual elements', () => {
  const markup = renderToStaticMarkup(<ReleaseNotes notes={notes}/>)
  expect(markup).toContain('<p>0.1.0-rc.6</p>')
  expect(markup.match(/<h5>/g)).toHaveLength(6)
  expect(markup.match(/<ul>/g)).toHaveLength(6)
  expect(markup.match(/<li>/g)).toHaveLength(8)
  expect(markup).toContain('<h5>Known limitations</h5><ul><li>')
})

test('escapes markup supplied in headings, list items and paragraphs', () => {
  const markup = renderToStaticMarkup(<ReleaseNotes notes={'# <b>Title</b>\n- <img src=x>\n<script>alert(1)</script>'}/>)
  expect(markup).toContain('<h5>&lt;b&gt;Title&lt;/b&gt;</h5>')
  expect(markup).toContain('<li>&lt;img src=x&gt;</li>')
  expect(markup).toContain('<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>')
})
