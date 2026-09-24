import type { AudioEngine } from './audio';
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
    this.el.src = `${import.meta.env.BASE_URL}${t.src}`;
    this.el.load();
  }

  async play() {
    this.audio.unlock();
    if (this.tape.kind === 'spotify') {
      const c = await this.ensureSpotify();
      if (!c) return;
      c.loadUri(`spotify:track:${this.track.spotify}`);
      c.play();
      this.playing = true;
      this.emit();
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

  pause() {
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
      this.spotify.loadUri(`spotify:track:${this.track.spotify}`);
      this.spotify.play();
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
          this.playing = !e.data.isPaused;
          this.loading = false;
          this.emit();
        });
        this.loading = false;
        resolve(c);
      });
    });
  }
}
