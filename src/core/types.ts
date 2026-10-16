/** P3-01: stable pure-data contracts. No UI, storage or rules imports. */
export const SCHEMA_VERSION = 3 as const;
export const UPGRADE_RULES_VERSION = 1 as const;
export type CardKind = 'reward' | 'stride';
export type PlayerId = string;
export type TileKind = 'start' | 'property' | 'neutral';
export type Phase = 'setup' | 'await_roll' | 'await_decision' | 'await_end_turn' | 'finished';
export type PlayerKind = 'human' | 'computer';

export interface PlayerConfig { readonly id: PlayerId; readonly name: string; readonly kind?: PlayerKind; }
export interface TileConfig {
  readonly id: number;
  readonly kind: TileKind;
  readonly title: string;
  readonly price?: number;
  readonly rent?: number;
}
export interface GameConfig {
  readonly players: readonly PlayerConfig[];
  readonly tiles: readonly TileConfig[];
  readonly initialCash: number;
  readonly maxRounds: number;
  readonly upgrades?: { readonly costRates: readonly [number,number]; readonly rentRates: readonly [number,number,number] };
  readonly eventRules?: {readonly tileIds:readonly number[];readonly bonus:number;readonly fee:number};
  readonly cardRules?: {readonly tileIds:readonly number[];readonly rewardCash:number;readonly moveBonus:number;readonly maxHand:number};
}
export interface Player {
  readonly id: PlayerId;
  readonly name: string;
  readonly kind: PlayerKind;
  readonly position: number;
  readonly cash: number;
  readonly bankrupt: boolean;
  readonly cards?:Readonly<Record<CardKind,number>>;
}
export interface Tile extends TileConfig {
  readonly ownerId: PlayerId | null;
  readonly level?: number;
  readonly upgradeCosts?: readonly [number,number];
  readonly levelRents?: readonly [number,number,number];
  readonly eventBonus?:number;
  readonly eventFee?:number;
  readonly cardStation?:boolean;
}
export interface GameEvent {
  readonly type: 'game_started' | 'die_rolled' | 'player_moved' | 'turn_ended' | 'tile_landed' | 'property_declined' | 'property_bought' | 'property_upgraded' | 'event_bonus' | 'event_fee' | 'card_received' | 'card_used' | 'rent_paid' | 'player_bankrupt' | 'game_finished';
  readonly actorId?: PlayerId;
  readonly details?: Readonly<Record<string, string | number>>;
}
export interface GameState {
  readonly schemaVersion: typeof SCHEMA_VERSION;
  readonly upgradeRulesVersion: typeof UPGRADE_RULES_VERSION;
  readonly cardRules?: {readonly rewardCash:number;readonly moveBonus:number;readonly maxHand:number};
  readonly pendingMoveBonus?:number;
  readonly status: 'setup' | 'playing' | 'finished';
  readonly phase: Phase;
  readonly revision: number;
  readonly round: number;
  readonly currentPlayerIndex: number;
  readonly randomState: number;
  readonly maxRounds: number;
  readonly players: readonly Player[];
  readonly tiles: readonly Tile[];
  readonly winnerId: PlayerId | null;
  readonly events: readonly GameEvent[];
}
export type GameAction =
  | { readonly type: 'start_game'; readonly actorId: PlayerId }
  | { readonly type: 'roll'; readonly actorId: PlayerId }
  | { readonly type: 'buy_property'; readonly actorId: PlayerId }
  | { readonly type: 'decline_property'; readonly actorId: PlayerId }
  | { readonly type: 'end_turn'; readonly actorId: PlayerId }
  | { readonly type: 'upgrade_property'; readonly actorId: PlayerId; readonly tileId: number }
  | { readonly type: 'use_card'; readonly actorId:PlayerId; readonly cardType:CardKind; readonly targetId?:PlayerId };
export type RejectReason = 'INVALID_PHASE' | 'INVALID_ACTOR' | 'INSUFFICIENT_FUNDS';
export type ActionResult =
  | { readonly ok: true; readonly state: GameState; readonly events: readonly GameEvent[] }
  | { readonly ok: false; readonly state: GameState; readonly events: readonly []; readonly reason: RejectReason };

