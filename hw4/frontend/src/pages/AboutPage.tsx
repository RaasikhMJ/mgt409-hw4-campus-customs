import { useEffect } from 'react'

export function AboutPage() {
  useEffect(() => {
    document.title = 'About Us · Campus Customs'
  }, [])

  return (
    <section className="page about">
      <p className="kicker">The house</p>
      <h1>
        Daylight shop. <em>Night edit.</em>
      </h1>
      <div className="about-grid">
        <p>
          Campus Customs has kept a Yale counter on Broadway since 1975, opened
          by a father across from campus and carried by the next generation.
          The shop people already know sells Bulldog Blue the comfortable way:
          crest, game day, a hoodie you can live in.
        </p>
        <p>
          This floor is the after-hours cut of that same house. The pieces are
          the catalogue, not a costume. Navy still does the talking. The fit
          just expects you to leave the library.
        </p>
      </div>
      <aside className="visit">
        <p>Come by the counter</p>
        <strong>57 Broadway, New Haven</strong>
      </aside>
    </section>
  )
}
