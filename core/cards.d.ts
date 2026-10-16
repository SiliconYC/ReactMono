/** Deterministic single-command strategy cards. Illegal attempts are immutable. */
import type { GameState, Player, GameAction, ActionResult, CardKind } from './types.js';
export declare const CARD_NAMES: Readonly<Record<CardKind, string>>;
/** The hand limit counts all existing and newly acquired cards. */
export declare function handSize(cards: Player['cards']): number;
export declare function useCard(state: GameState, actor: Player, action: Extract<GameAction, {
    type: 'use_card';
}>): ActionResult;
