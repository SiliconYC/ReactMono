/** 纯数据的 v1 对局存档契约；不触碰浏览器、React、文件系统。 */
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
/** 校验当前规则 v1 的每一项持久化字段，避免不完整对象影响回合结算。 */
export declare function validateGameState(value: unknown): asserts value is GameState;
export declare function serializeGame(game: GameState, options?: {
    readonly createdAt?: string;
    readonly now?: string;
}): string;
export declare function deserializeGame(raw: string): SaveEnvelope;
