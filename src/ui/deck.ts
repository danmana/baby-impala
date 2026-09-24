import { h, svg, ICONS } from './dom';
import type { MusicPlayer, DeckState } from '../audio/music';

const fmt = (s: number) => {
  if (!isFinite(s) || s <= 0) return '0:00';
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
};

/**
 * A compact copy of Baby's aftermarket slot-loading deck: FM/AM dial window,
 * a horizontal slot showing the hand-labelled edge of the tape, chunky olive
 * push buttons. Always on screen, so nobody has to reach into the car.
 */
export class Deck {
  readonly el: HTMLElement;
  private label: HTMLElement;
  private cassette: HTMLElement;
  private needle: HTMLElement;
  private dial: HTMLElement;
  private title: HTMLElement;
  private meta: HTMLElement;
  private mobile: HTMLElement;
  private playBtn: HTMLButtonElement;
  private led: HTMLElement;
  private lastTape = '';

  constructor(host: HTMLElement, private player: MusicPlayer) {
    const btn = (icon: string, label: string, run: () => void) => {
      const b = h('button', { class: 'btn', type: 'button', 'aria-label': label, title: label });
      b.innerHTML = icon;
      b.addEventListener('click', () => {
        b.classList.add('pressed');
        setTimeout(() => b.classList.remove('pressed'), 140);
        run();
      });
      return b;
    };
    this.needle = h('div', { class: 'needle' });
    this.dial = h('div', { class: 'dial' },
      h('div', { class: 'scale fm' }, ...['88', '94', '98', '103', '106', '108'].map((n) => h('span', {}, n))),
      h('div', { class: 'scale am' }, ...['54', '70', '100', '130', '170'].map((n) => h('span', {}, n))),
      this.needle);
    this.playBtn = btn(ICONS.play, 'Play', () => player.toggle());
    this.label = h('div', { class: 'label' });
    this.cassette = h('div', { class: 'cassette' }, this.label);
    this.led = h('span', { class: 'led', 'aria-hidden': 'true' });
    this.title = h('b', {});
    this.meta = h('small', {});
    this.mobile = h('div', { class: 'mobile-song' });
    const spotHost = h('div', { class: 'spotify', hidden: true });
    player.spotifyHost = spotHost;
    this.el = h('section', { class: 'deck', 'aria-label': 'Tape deck' },
      h('div', { class: 'unit' },
        h('div', { class: 'row' }, btn(ICONS.prev, 'Previous song', () => player.prev()), this.dial, btn(ICONS.next, 'Next song', () => player.next())),
        h('div', { class: 'row slotrow' },
          this.playBtn,
          h('div', { class: 'slot' }, h('div', { class: 'flap' }), this.cassette),
          btn(ICONS.eject, 'Switch cassette', () => this.eject()),
        ),
        h('div', { class: 'row', style: 'margin-top:7px;justify-content:space-between' },
          h('span', { class: 'brand' }, 'Hunter 2000'), this.led),
        this.mobile,
      ),
      h('div', { class: 'song paper' }, h('span', { class: 'tape' }), this.title, this.meta),
      spotHost,
    );
    host.append(this.el);
    player.onUpdate = (s) => this.render(s);
    this.render(player.state());
  }

  private eject() {
    this.cassette.classList.add('out');
    setTimeout(() => {
      this.player.switchTape();
      this.cassette.classList.remove('out');
    }, 420);
  }

  setLit(on: boolean) {
    this.dial.classList.toggle('lit', on);
  }

  private render(s: DeckState) {
    if (s.tape.id !== this.lastTape) {
      this.lastTape = s.tape.id;
      this.label.textContent = `${s.tape.label.toLowerCase()} · ${s.tape.sub}`;
      this.cassette.style.setProperty('--stripe', s.tape.color);
    }
    this.playBtn.innerHTML = s.playing ? ICONS.pause : ICONS.play;
    this.playBtn.setAttribute('aria-label', s.playing ? 'Pause' : 'Play');
    this.led.classList.toggle('on', s.playing);
    this.title.textContent = s.track.title;
    const time = s.tape.kind === 'spotify' ? 'on Spotify' : `${fmt(s.position)} / ${fmt(s.duration)}`;
    this.meta.textContent = `${s.track.artist} · ${s.loading ? 'loading…' : time}`;
    this.mobile.replaceChildren(h('b', {}, s.track.title), s.track.artist);
    // the needle drifts across the band as the song plays
    const f = s.duration > 0 ? s.position / s.duration : 0;
    this.needle.style.left = `${8 + (s.trackIndex / s.tape.tracks.length + f / s.tape.tracks.length) * 84}%`;
  }
}

export { svg };
