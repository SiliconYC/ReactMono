/** Local versioned save contract; migrates historic two-player v1/v2 records. */
import { SCHEMA_VERSION, type GameState } from './game.js';
export declare const SAVE_FORMAT_VERSION: 1;
export declare const MAX_SAVE_CHARS = 4000000;
export type SaveErrorCode = 'INVALID_JSON' | 'TOO_LARGE' | 'INVALID_FORMAT' | 'INCOMPATIBLE_VERSION' | 'INVALID_STATE' | 'INVALID_CHECKSUM';
export declare class SaveError extends Error {
    readonly code: SaveErrorCode;
    constructor(code: SaveErrorCode, message: string);
}
export interface SaveEnvelope {
    readonly format: 'reactmono-save';
    readonly formatVersion: typeof SAVE_FORMAT_VERSION;
    readonly rulesVersion: typeof SCHEMA_VERSION;
    readonly createdAt: string;
    readonly updatedAt: string;
    readonly game: GameState;
    readonly checksum: string;
}
/** Validate current and migrated legacy states against the same strict bounds. */
export declare function validateGameState(value: unknown, expectedVersion?: number): asserts value is GameState;
export declare function serializeGame(game: GameState, options?: {
    readonly createdAt?: string;
    readonly now?: string;
}): string;
export declare function deserializeGame(raw: string): SaveEnvelope;
