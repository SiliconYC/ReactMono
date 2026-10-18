import { type GameAction, type GameConfig, type GameEvent, type GameState, type RejectReason } from '../core/game.js';
export declare const DEMO_CONFIG: GameConfig;
export type AcceptedDemoCommand = {
    readonly ok: true;
    readonly before: GameState;
    readonly after: GameState;
    readonly events: readonly GameEvent[];
    readonly dieValue: number | null;
    readonly route: readonly number[];
};
export type RejectedDemoCommand = {
    readonly ok: false;
    readonly before: GameState;
    readonly after: GameState;
    readonly events: readonly [];
    readonly dieValue: null;
    readonly route: readonly [];
    readonly reason: RejectReason;
};
export type DemoCommandResult = AcceptedDemoCommand | RejectedDemoCommand;
export declare function createDemoGame(seed: number, maxRounds?: number): GameState;
export declare function dispatchDemoAction(state: GameState, action: GameAction): DemoCommandResult;
/** Share a reproducible real game without embedding snapshots or synthetic outcomes. */
export declare function demoSeedFromSearch(search: string): number;
/** Optional normal game length, kept bounded for shareable demo sessions. */
export declare function demoRoundsFromSearch(search: string): number;
