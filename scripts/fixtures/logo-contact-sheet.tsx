import React from 'react'
import { createRoot } from 'react-dom/client'
import { PlatformMark } from '../../src/ui/PlatformMark'
import '../../src/styles.css'

const groups = {
  'Community and social': ['mastodon.social','mastodon.online','mstdn.party','lemmy.ml','Bluesky','Reddit','YouTube','TikTok'],
  'Publishing and entertainment': ['Wattpad','Medium','LibraryThing','LiveJournal','Mixcloud','Spotify','Kongregate','Letterboxd'],
  'Development and professional': ['GitHub','Codeberg','LeetCode','Laracast','kwork','LinkedIn','iNaturalist','Hugging Face'],
  'Software families and fallback': ['arcgit.wpi.edu','8cubes.com','git.gay','1160.theshizz.org','bbs.6ebook.com','Steam Community (User)','Docker Hub','Unlisted fixture'],
}
createRoot(document.querySelector('main')!).render(<>
  <h1>Platform logos</h1>
  {Object.entries(groups).map(([category,names]) => <section key={category}>
    <h2>{category}</h2><div className="samples">{names.map(name => <div className="sample" key={name}>
      <PlatformMark name={name}/><span>{name}</span>
    </div>)}</div>
  </section>)}
</>)
