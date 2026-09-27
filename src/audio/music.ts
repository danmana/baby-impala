import type { AudioEngine } from './audio';
import { assetUrl } from '../boot/assets';
import { TAPES, type Tape, type Track } from '../content/lore';

interface SpotifyController {
  loadUri(uri: string): void;
  play(): void;
  pause(): void;
  resume(): void;
  togglePlay(): void;
  addListener(ev: string, cb: (e: { data: { isPaused: boolean; position: number; duration: number } }) => void): void;
  destroy(): void;
}
interface SpotifyIFrameAPI {
  createController(el: HTMLElement, opts: Record<string, unknown>, cb: (c: SpotifyController) => void): void;
}

export interface DeckState {
  tape: Tape;
  track: Track;
  trackIndex: number;
  playing: boolean;
  position: number;
  duration: number;
  loading: boolean;
  /** a short note for the song label, when something needs saying */
  hint: string | null;
}

/**
 * Dean's tapes. Local tapes are royalty-free MP3s played through the Web
 * Audio graph; "The Real Deal" plays the actual songs from the show through
 * Spotify's embed (full tracks when logged in to Spotify, previews otherwise).
 */
export class MusicPlayer {
  tapeIndex = 0;
  trackIndex = 0;
  playing = false;
  private el = new Audio();
  private src: MediaElementAudioSourceNode | null = null;
  private spotify: SpotifyController | null = null;
  private spotifyPos = 0;
  private spotifyDur = 0;
  private spotifyReady: Promise<SpotifyIFrameAPI> | null = null;
  loading = false;
  private hint: string | null = null;
  private stall = 0;
  private userPaused = false;
  private endTimer = 0;
  private lastSpotifyPos = 0;
  onUpdate: ((s: DeckState) => void) | null = null;
  spotifyHost: HTMLElement | null = null;

  constructor(private audio: AudioEngine) {
    this.el.preload = 'none';
    this.el.addEventListener('ended', () => this.next(true));
    this.el.addEventListener('timeupdate', () => this.emit());
    this.el.addEventListener('playing', () => { this.loading = false; this.emit(); });
    this.el.addEventListener('waiting', () => { this.loading = true; this.emit(); });
  }

  get tape() { return TAPES[this.tapeIndex]; }
  get track() { return this.tape.tracks[this.trackIndex]; }

  state(): DeckState {
    const spot = this.tape.kind === 'spotify';
    return {
      tape: this.tape, track: this.track, trackIndex: this.trackIndex, playing: this.playing,
      position: spot ? this.spotifyPos : this.el.currentTime || 0,
      duration: spot ? this.spotifyDur : this.el.duration || this.track.seconds || 0,
      loading: this.loading,
      hint: this.hint,
    };
  }

  private emit() { this.onUpdate?.(this.state()); }

  private connect() {
    if (this.src || !this.audio.ctx) return;
    this.src = this.audio.ctx.createMediaElementSource(this.el);
    this.src.connect(this.audio.music);
  }

  private loadLocal() {
    const t = this.track;
    if (!t.src) return;
    this.el.src = assetUrl(t.src);
    this.el.load();
  }

  async play() {
    this.audio.unlock();
    if (this.tape.kind === 'spotify') {
      const c = await this.ensureSpotify();
      if (!c) return;
      this.startSpotify(c);
      return;
    }
    this.connect();
    if (!this.el.src) this.loadLocal();
    this.loading = true;
    this.playing = true;
    this.emit();
    try {
      await this.el.play();
    } catch {
      this.playing = false;
      this.loading = false;
    }
    this.emit();
  }

  /**
   * Ask the embed to play and wait for it to say so. The deck only lights up
   * on Spotify's own playback updates; if nothing starts (the browser blocked
   * it, or the track has no preview), say so instead of sitting there silent.
   */
  private startSpotify(c: SpotifyController) {
    clearTimeout(this.endTimer);
    this.userPaused = false;
    this.lastSpotifyPos = 0;
    c.loadUri(`spotify:track:${this.track.spotify}`);
    c.play();
    this.hint = null;
    this.loading = true;
    this.emit();
    clearTimeout(this.stall);
    this.stall = window.setTimeout(() => {
      if (this.playing) return;
      this.loading = false;
      this.hint = 'press play in the Spotify player';
      this.emit();
    }, 6000);
  }

  pause() {
    clearTimeout(this.stall);
    clearTimeout(this.endTimer);
    this.userPaused = true;
    if (this.tape.kind === 'spotify') this.spotify?.pause();
    else this.el.pause();
    this.playing = false;
    this.emit();
  }

  toggle() {
    if (this.playing) this.pause();
    else void this.play();
  }

  next(auto = false) {
    this.trackIndex = (this.trackIndex + 1) % this.tape.tracks.length;
    this.changeTrack(auto || this.playing);
  }

  prev() {
    if (this.tape.kind === 'local' && this.el.currentTime > 4) {
      this.el.currentTime = 0;
      return;
    }
    this.trackIndex = (this.trackIndex - 1 + this.tape.tracks.length) % this.tape.tracks.length;
    this.changeTrack(this.playing);
  }

  private changeTrack(resume: boolean) {
    if (this.tape.kind === 'local') {
      this.loadLocal();
      if (resume) void this.play();
    } else if (this.spotify && resume) {
      this.startSpotify(this.spotify);
    } else if (this.spotify) {
      this.spotify.loadUri(`spotify:track:${this.track.spotify}`);
    }
    this.emit();
  }

  /** Eject and slot the next cassette. */
  switchTape(index?: number) {
    const wasPlaying = this.playing;
    this.pause();
    this.tapeIndex = index ?? (this.tapeIndex + 1) % TAPES.length;
    this.trackIndex = 0;
    this.el.removeAttribute('src');
    this.el.load();
    this.hint = null;
    if (this.tape.kind !== 'spotify') this.teardownSpotify();
    this.emit();
    if (wasPlaying || this.tape.kind === 'spotify') void this.play();
  }

  private teardownSpotify() {
    this.spotify?.destroy();
    this.spotify = null;
    if (this.spotifyHost) this.spotifyHost.hidden = true;
  }

  private loadSpotifyApi(): Promise<SpotifyIFrameAPI> {
    if (!this.spotifyReady) {
      this.spotifyReady = new Promise((resolve) => {
        (window as unknown as { onSpotifyIframeApiReady: (api: SpotifyIFrameAPI) => void }).onSpotifyIframeApiReady =
          (api) => resolve(api);
        const s = document.createElement('script');
        s.src = 'https://open.spotify.com/embed/iframe-api/v1';
        s.async = true;
        document.head.appendChild(s);
      });
    }
    return this.spotifyReady;
  }

  private async ensureSpotify(): Promise<SpotifyController | null> {
    if (this.spotify) return this.spotify;
    if (!this.spotifyHost) return null;
    this.loading = true;
    this.emit();
    const api = await this.loadSpotifyApi();
    this.spotifyHost.hidden = false;
    const mount = document.createElement('div');
    this.spotifyHost.replaceChildren(mount);
    return new Promise((resolve) => {
      api.createController(mount, { uri: `spotify:track:${this.track.spotify}`, width: '100%', height: 80, theme: 0 }, (c) => {
        this.spotify = c;
        c.addListener('playback_update', (e) => {
          this.spotifyPos = e.data.position / 1000;
          this.spotifyDur = e.data.duration / 1000;
          const was = this.playing;
          this.playing = !e.data.isPaused;
          if (this.playing) {
            this.loading = false;
            this.hint = null;
          }
          // a track (or its 30-second preview) ran out on its own: on to the next, like a tape
          const nearEnd = this.spotifyDur > 0 && (this.spotifyPos >= this.spotifyDur - 1 || this.spotifyPos === 0);
          if (was && !this.playing && !this.userPaused && nearEnd && this.lastSpotifyPos >= this.spotifyDur - 2) {
            this.next(true);
            return;
          }
          this.lastSpotifyPos = this.spotifyPos;
          // some previews end on a last "still playing" update at the very end and
          // then go quiet: if nothing follows, treat that as the end too
          clearTimeout(this.endTimer);
          if (this.playing && this.spotifyDur > 0 && this.spotifyPos >= this.spotifyDur - 0.4) {
            this.endTimer = window.setTimeout(() => {
              if (this.playing && !this.userPaused && this.tape.kind === 'spotify') this.next(true);
            }, 1500);
          }
          this.emit();
        });
        this.loading = false;
        resolve(c);
      });
    });
  }
}
