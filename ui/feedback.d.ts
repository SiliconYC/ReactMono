import type { GameEvent, GameState } from '../core/game.js';
export interface VisualCue {
    readonly text: string;
    readonly tone: 'move' | 'money' | 'card' | 'danger' | 'finish' | 'dice' | 'normal';
    readonly revision: number;
    readonly actorId: string | null;
    readonly path: readonly number[];
    readonly step: number;
}
export declare function walkPath(before: GameState, after: GameState, actorId: string): number[];
export declare function eventCue(before: GameState, after: GameState, events: readonly GameEvent[]): VisualCue | null;
