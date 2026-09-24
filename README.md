# Baby

An unofficial fan page for **Baby**, Dean Winchester's black 1967 Chevrolet Impala four-door hardtop from *Supernatural*.

Walk around her on a patch of wet asphalt at night, start the engine, sweep the A-pillar spotlights through the fog, open the trunk to see the Winchester arsenal under the Devil's Trap, climb inside to find the army man and the Legos, pull her apart in an exploded workshop view, and play Dean's tapes on a copy of her slot-loading deck.

Built with [three.js](https://threejs.org) and Vite. Everything the site needs ships in this repo; the one external service is the optional Spotify tape.

## Running it

```bash
npm install
npm run dev        # http://localhost:5177
npm run build      # production build into dist/
```

Handy URL flags while developing: `?autostart` skips the start screen, `?nointro` skips the reveal, `?quality=low|medium|high` forces a quality tier.

## What's in here

| Path | What it is |
| --- | --- |
| `src/scene/` | Renderer, lighting, the wet ground with planar puddle reflections, fog, dust, rain, the motel, the camera director, the exploded view and the trunk sequence |
| `src/ui/` | The journal UI: loading page, index tabs, the checklist, lore pages, sigil hotspots, the cassette deck |
| `src/audio/` | Synthesised V8 start-up and idle, the trunk creak, and the tape player (local MP3s + Spotify embed) |
| `src/content/lore.ts` | Every piece of text on the site: hotspot lore, the trunk inventory, the Devil's Trap, the tapes |
| `tools/blender/` | The Blender build that turns the base model into Baby and exports `public/models/baby.glb` |
| `assets-src/sketchfab/` | The unmodified base model (glTF + textures) the Blender build starts from |
| `docs/research.md` | Research notes: trivia with episode references, trunk inventory, music |

### Rebuilding the car

```bash
npm run model                        # needs Blender 5.x at /Applications/Blender.app
BABY_PREVIEW=1 npm run model         # also renders preview stills into .work/
```

The Blender build scales and orients the base model, then turns it into Baby:

- cuts the one-piece shell into hood, trunk lid and four doors along the real shut lines so they can open and explode apart
- swaps the mag wheels for her polished 15" dished wheels with the ring of holes
- adds the two A-pillar spotlights and the second exhaust pipe; removes the rear script and the passenger mirror
- builds the trunk: the false floor that stands up like a pegboard with the weapons strapped to its felt, the grey tray of gear, and the painted Devil's Trap on the underside of the lid
- adds the 327 V8 and engine bay, the slot-loading tape deck, the Legos in the defroster vent, the army man in the rear ashtray and the carved "D.W." / "S.W."

## Credits

- **Base 3D model:** ["Chevrolet Impala 1967"](https://sketchfab.com/3d-models/chevrolet-impala-1967-bce35ef0c10d41fdb3f7d8c4225144d2) by [Eques_inferno](https://sketchfab.com/Eques_inferno), licensed under [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/). Adapted: re-scaled, split into panels, parts removed and added as described above.
- **Music (local tapes):** Kevin MacLeod ([incompetech.com](https://incompetech.com)), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): "Big Rock", "Twisted", "Gearhead", "Hotrock", "Neolith", "Slow Burn", "Matt's Blues", "OctoBlues", "Hustle", "Nile's Blues", "Metalmania", "Cool Rock", "Noise Attack", "Exhilarate", "Motherlode". Re-encoded at 96 kbps with loudness normalisation.
- **Music ("The Real Deal" tape):** the actual songs from the show, streamed through Spotify's embed player. Nothing is hosted here.
- **Fonts:** League Gothic (SIL OFL), Special Elite (Apache 2.0), Reenie Beanie (SIL OFL). Licence files sit next to the fonts.
- **Reference images:** collected mostly from [thespnreferencedesk](https://www.tumlook.com/thespnreferencedesk) and Reddit. They live in `references/` and were used for modelling only; none of them appear on the site.

Made by [@danmana](https://x.com/danmana) and [Opus 5.5](https://www.anthropic.com/claude-opus-5-5).

*Unofficial fan page. Not affiliated with Warner Bros., The CW or the creators of Supernatural.*
