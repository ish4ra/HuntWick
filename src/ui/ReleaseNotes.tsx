import type { ReactNode } from 'react'

// Only headings, paragraphs, ordered and unordered lists are interpreted.
// Remote text stays in React text nodes, including HTML and image/link syntax.
export function ReleaseNotes({ notes }: { notes: string }) {
  const blocks: ReactNode[] = []
  let lines: string[] = []
  let kind = 'paragraph'
  let start = 1
  function flush() {
    if (!lines.length) return
    const key = blocks.length
    const items = lines.map((text, i) => <li key={i}>{text}</li>)
    if (kind === 'ordered') blocks.push(<ol key={key} start={start}>{items}</ol>)
    else if (kind === 'unordered') blocks.push(<ul key={key}>{items}</ul>)
    else blocks.push(<p key={key}>{lines.join(' ')}</p>)
    lines = []
  }
  for (const raw of notes.split(/\r?\n/)) {
    const line = raw.trim()
    const heading = /^#{1,6}\s+(.+)$/.exec(line)
    if (!line || heading) {
      flush()
      if (heading) blocks.push(<h5 key={blocks.length}>{heading[1]}</h5>)
      continue
    }
    const list = /^(?:([-+*])|(\d{1,9})[.)])\s+(.+)$/.exec(line)
    const next = list ? (list[1] ? 'unordered' : 'ordered') : 'paragraph'
    if (kind !== next) flush()
    if (!lines.length && list?.[2]) start = Number(list[2])
    kind = next
    lines.push(list ? list[3] : line)
  }
  flush()
  return <div className="release-notes">{blocks.length ? blocks : <p>No release notes supplied.</p>}</div>
}
