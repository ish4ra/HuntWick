import { Globe2 } from 'lucide-react'
import mappings from '../platformLogos.generated.json'

// Exact instance identities retain punctuation. Brand aliases tolerate spelling variants.
const instances = new Map(Object.entries(mappings.instances))
const brands = new Map(Object.entries(mappings.brands))
export function resolvePlatformLogo(name: string): string | undefined {
  const key = name.trim().toLowerCase()
  const brandKey = key.normalize('NFKD').replace(/\p{M}/gu, '').replace(/[^a-z0-9]/g, '')
  return instances.get(key) ?? brands.get(brandKey)
}

export function PlatformMark({ name }: { name: string }) {
  const icon = resolvePlatformLogo(name)
  if (!icon) return <span aria-hidden="true" className="platform-mark"><Globe2 size={16} /></span>
  if (icon === 'flarum') {
    return <img className="brand-mark brand-original" src="/platforms/flarum.png" alt="" />
  }
  if (icon === 'laracasts') {
    return <span className="brand-mark laracasts-mark" aria-hidden="true" />
  }
  const mask = `url("/platforms/${icon}.svg")`
  return <span aria-hidden="true" className={icon === 'kongregate' ? 'brand-mark kongregate-mark' : 'brand-mark'}
    style={{maskImage: mask, WebkitMaskImage: mask}} />
}
