import { propertyVisitAvailable, quotePropertyUpgrade, type GameState } from '../core/game.js';

export const HUMAN_CONTINUE_DELAY = 4000;

export interface HumanContinueContext {
  readonly armedTurn: string | null;
  readonly managedTurn: string | null;
  readonly blocked: boolean;
}

export function humanTurnKey(game: GameState): string {
  return `${game.round}:${game.players[game.currentPlayerIndex].id}`;
}

export function canAutoContinue(game: GameState, context: HumanContinueContext): boolean {
  const player = game.players[game.currentPlayerIndex];
  if (game.status !== 'playing' || game.phase !== 'await_end_turn' || player.kind !== 'human' ||
      context.blocked || context.armedTurn !== humanTurnKey(game) || context.managedTurn === humanTurnKey(game)) return false;
  const target = game.tiles[player.position];
  return !(target.ownerId === player.id && !target.mortgaged &&
    quotePropertyUpgrade(game, target.id) !== null && propertyVisitAvailable(game, player, target.id));
}

export function canCommitAutoContinue(snapshot: GameState, current: GameState, context: HumanContinueContext): boolean {
  // 读档和重开可能具有相同的轮次、玩家、revision；对象身份才能使旧回调失效。
  return snapshot === current && canAutoContinue(current, context);
}
