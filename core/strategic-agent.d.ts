/** P3-13: deterministic policies. Read-only snapshots in; engine commands out. */
import type { GameAction, GameState, ComputerStyle } from './types.js';
export declare const COMPUTER_STYLES: readonly ComputerStyle[];
export declare const COMPUTER_STYLE_NAMES: Readonly<Record<ComputerStyle, string>>;
export declare function chooseStyledAction(state: GameState, style: ComputerStyle): GameAction | null;
