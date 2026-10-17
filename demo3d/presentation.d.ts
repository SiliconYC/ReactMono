import type { GameEvent } from '../core/game.js';
export type RentCue = Readonly<{
    fromId: string;
    toId: string;
    tileId: number;
    amount: number;
}>;
export declare function rentCueFor(events: readonly GameEvent[]): RentCue | null;
