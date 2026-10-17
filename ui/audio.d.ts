import type { GameEvent } from '../core/game.js';
export type SoundKind = 'dice' | 'step' | 'gain' | 'pay' | 'card' | 'facility' | 'finish';
export declare function classifySound(events: readonly GameEvent[]): SoundKind | null;
/** All sound comes from tiny locally synthesized Web Audio oscillators; no copyrighted samples. */
export declare class SoundController {
    private ctx;
    private lastAt;
    private enabled;
    private volume;
    constructor();
    get isEnabled(): boolean;
    get level(): number;
    setVolume(value: number): void;
    setEnabled(value: boolean): Promise<void>;
    activate(): Promise<void>;
    play(events: readonly GameEvent[]): void;
    dispose(): void;
}
