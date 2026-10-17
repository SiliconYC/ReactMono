import type { GameAction, GameEvent, GameState } from '../core/game.js';
export type Pace = 'normal' | 'fast';
/** Pure pacing, never participate in action choice or random-state changes. */
export declare function cpuDelay(pace: Pace, action: GameAction, events?: readonly GameEvent[]): number;
export declare const MAX_CPU_ACTIONS_PER_TURN = 48;
export type CpuTiming = {
    readonly decisions: number;
    readonly calculationMs: number;
    readonly waitScheduledMs: number;
    readonly lastCalculationMs: number;
    readonly longCalculationCount: number;
};
export declare const initialCpuTiming: CpuTiming;
export declare function addCpuTiming(t: CpuTiming, calculationMs: number, nextDelay: number): CpuTiming;
export declare function cpuTurnKey(state: GameState): string;
