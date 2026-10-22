/** P3-01: stable pure-data contracts. No UI, storage or rules imports. */
import type { StockMarket, StockId } from './market.js';
export const SCHEMA_VERSION = 4 as const;
export const UPGRADE_RULES_VERSION = 1 as const;
export type CardKind = 'reward' | 'stride' | 'remote' | 'roadblock' | 'rent_free';
export type CardHand = Readonly<{reward:number;stride:number} & Partial<Record<'remote'|'roadblock'|'rent_free',number>>>;
export interface Roadblock {readonly tileId:number;readonly ownerId:PlayerId;readonly expiresRound:number;}
export type PlayerId = string;
export type FacilityKind='hospital'|'prison'|'shop';
export interface Detention {readonly kind:'hospital'|'prison';readonly remaining:number;}
export interface FacilityConfig {
  readonly hospitalTiles:readonly number[];readonly prisonTiles:readonly number[];readonly shopTiles:readonly number[];
  readonly hospitalTurns:number;readonly prisonTurns:number;readonly hospitalFee:number;readonly prisonFee:number;
  readonly prices:Readonly<Record<CardKind,number>>;readonly stock:Readonly<Record<CardKind,number>>;
}
export interface FacilityRules {readonly version:1;readonly hospitalTurns:number;readonly prisonTurns:number;readonly hospitalFee:number;readonly prisonFee:number;readonly prices:Readonly<Record<CardKind,number>>;}
export interface ShopStock {readonly tileId:number;readonly cards:Readonly<Record<CardKind,number>>;}
export type TileKind = 'start' | 'property' | 'neutral';
export type Phase = 'setup' | 'await_roll' | 'await_decision' | 'await_end_turn' | 'await_shop' | 'finished';
export type PlayerKind = 'human' | 'computer';
/** Optional so P1/P2/P3 historic saves remain byte-compatible. */
export type ComputerStyle = 'conservative' | 'balanced' | 'aggressive';

export interface PlayerConfig { readonly id: PlayerId; readonly name: string; readonly kind?: PlayerKind; readonly computerStyle?: ComputerStyle; }
export interface TileConfig {
  readonly id: number;
  readonly kind: TileKind;
  readonly title: string;
  readonly price?: number;
  readonly rent?: number;
}
export interface MapCell { readonly column:number; readonly row:number; }
/** Route lists tile IDs in cyclic walking order, starting at tile 0. */
export interface GameMap {
  readonly id:string;
  readonly version:number;
  readonly columns:number;
  readonly rows:number;
  readonly cells:readonly MapCell[];
  readonly route:readonly number[];
}
export interface ResaleRules { readonly landPercent:number; readonly upgradePercent:number; }
export interface LoanState { readonly version:1; readonly interestBps:number; readonly lastInterestRound:number; }
export interface BankState { readonly version:1; readonly interestBps:number; readonly lastInterestRound:number; }
export interface GameConfig {
  readonly terraceRulesVersion?: 1;
  /** Absent in historic games: retain their agreed round-limit settlement. */
  readonly endCondition?: 'bankruptcy';
  /** Optional classic-style construction: one buy/build/upgrade at the landed tile per visit. */
  readonly propertyVisitOnly?: boolean;
  /** Old games trade cash; opt-in bank trading keeps investment funds separate. */
  readonly stockAccount?: 'cash' | 'bank';
  /** Enable P3 strategy cards without changing legacy/P2 game semantics. */
  readonly strategyEnabled?: boolean;
  /** P3 facilities opt-in; depends on enabled strategy cards. */
  readonly specialEnabled?: boolean;
  readonly facilityConfig?:FacilityConfig;
  readonly bankEnabled?: boolean;
  readonly loanEnabled?: boolean;
  readonly loanInterestBps?: number;
  readonly bankInterestBps?: number;
  /** Optional deterministic virtual exchange, separate from the dice RNG. */
  readonly marketEnabled?: boolean;
  /** Opt in to deterministic resale-based rent rescue; old saves keep P2 behaviour. */
  readonly automaticLiquidation?:boolean;
  /** Optional deterministic resale percentages; old saves use stable defaults. */
  readonly resaleRules?:ResaleRules;
  readonly map?:GameMap;
  readonly players: readonly PlayerConfig[];
  readonly tiles: readonly TileConfig[];
  readonly initialCash: number;
  readonly maxRounds: number;
  readonly upgrades?: { readonly costRates: readonly [number,number]; readonly rentRates: readonly [number,number,number] };
  readonly eventRules?: {readonly tileIds:readonly number[];readonly bonus:number;readonly fee:number};
  readonly cardRules?: {readonly tileIds:readonly number[];readonly rewardCash:number;readonly moveBonus:number;readonly maxHand:number};
}
export interface StockHolding { readonly quantity:number; readonly costBasis:number; }
export type StockHoldings = Readonly<Partial<Record<StockId,StockHolding>>>;
export interface Player {
  readonly id: PlayerId;
  readonly name: string;
  readonly kind: PlayerKind;
  readonly computerStyle?: ComputerStyle;
  readonly position: number;
  readonly cash: number;
  /** Optional for legacy states; enabled games always initialize to zero. */
  readonly bankBalance?: number;
  readonly loanBalance?: number;
  readonly holdings?: StockHoldings;
  readonly bankrupt: boolean;
  readonly cards?:CardHand;
  readonly detention?:Detention;
}
export interface Tile extends TileConfig {
  readonly ownerId: PlayerId | null;
  readonly level?: number;
  readonly mortgaged?: true;
  readonly upgradeCosts?: readonly [number,number];
  readonly levelRents?: readonly [number,number,number];
  readonly eventBonus?:number;
  readonly eventFee?:number;
  readonly cardStation?:boolean;
  readonly facility?:FacilityKind;
}
export interface GameEvent {
  readonly type: 'facility_entered' | 'detention_skipped' | 'detention_released' | 'shop_purchased' | 'shop_left' | 'roadblock_triggered' | 'rent_waived' | 'card_expired' | 'game_started' | 'die_rolled' | 'player_moved' | 'turn_ended' | 'tile_landed' | 'property_declined' | 'property_bought' | 'property_upgraded' | 'property_sold' | 'property_liquidated' | 'bank_deposited' | 'bank_withdrawn' | 'bank_interest' | 'property_mortgaged' | 'property_released' | 'loan_borrowed' | 'loan_repaid' | 'loan_interest' | 'loan_default' | 'stock_bought' | 'stock_sold' | 'stock_liquidated' | 'event_bonus' | 'event_fee' | 'card_received' | 'card_used' | 'rent_paid' | 'player_bankrupt' | 'game_finished';
  readonly actorId?: PlayerId;
  readonly details?: Readonly<Record<string, string | number>>;
}
export interface GameState {
  readonly terraceRulesVersion?: 1;
  readonly endCondition?: 'bankruptcy';
  readonly propertyVisitOnly?: true;
  readonly stockAccount?: 'bank';
  readonly schemaVersion: typeof SCHEMA_VERSION;
  readonly upgradeRulesVersion: typeof UPGRADE_RULES_VERSION;
  readonly cardRules?: {readonly rewardCash:number;readonly moveBonus:number;readonly maxHand:number};
  readonly pendingMoveBonus?:number;
  readonly strategyEnabled?:true;
  readonly specialEnabled?:true;
  readonly facilityRules?:FacilityRules;
  readonly shops?:readonly ShopStock[];
  /** Zero means no remote die selected; valid pending values are 1–6. */
  readonly pendingDie?:number;
  readonly pendingRentWaiver?:boolean;
  readonly roadblocks?:readonly Roadblock[];
  readonly status: 'setup' | 'playing' | 'finished';
  readonly phase: Phase;
  readonly revision: number;
  readonly round: number;
  readonly currentPlayerIndex: number;
  readonly randomState: number;
  readonly maxRounds: number;
  readonly map: GameMap;
  readonly market?: StockMarket;
  readonly bank?: BankState;
  readonly loan?: LoanState;
  /** Undefined preserves pre-P3-06 rent behaviour, including old saved games. */
  readonly automaticLiquidation?:true;
  readonly resaleRules?:ResaleRules;
  readonly players: readonly Player[];
  readonly tiles: readonly Tile[];
  readonly winnerId: PlayerId | null;
  readonly events: readonly GameEvent[];
}
export type GameAction =
  | { readonly type: 'start_game'; readonly actorId: PlayerId }
  | { readonly type: 'roll'; readonly actorId: PlayerId }
  | { readonly type: 'skip_turn' | 'leave_shop'; readonly actorId:PlayerId }
  | { readonly type: 'buy_shop_card'; readonly actorId:PlayerId; readonly cardType:CardKind }
  | { readonly type: 'buy_property'; readonly actorId: PlayerId }
  | { readonly type: 'decline_property'; readonly actorId: PlayerId }
  | { readonly type: 'end_turn'; readonly actorId: PlayerId }
  | { readonly type: 'upgrade_property'; readonly actorId: PlayerId; readonly tileId: number }
  | { readonly type: 'sell_property'; readonly actorId: PlayerId; readonly tileId: number }
  | { readonly type: 'mortgage_property' | 'release_mortgage'; readonly actorId: PlayerId; readonly tileId:number }
  | { readonly type: 'buy_stock' | 'sell_stock'; readonly actorId:PlayerId; readonly stockId:StockId; readonly quantity:number }
  | { readonly type: 'borrow_loan' | 'repay_loan'; readonly actorId: PlayerId; readonly amount:number }
  | { readonly type: 'deposit_bank' | 'withdraw_bank'; readonly actorId: PlayerId; readonly amount:number }
  | { readonly type: 'use_card'; readonly actorId:PlayerId; readonly cardType:CardKind; readonly targetId?:PlayerId; readonly dieValue?:number; readonly tileId?:number };
export type RejectReason = 'INVALID_PHASE' | 'INVALID_ACTOR' | 'INSUFFICIENT_FUNDS';
export type ActionResult =
  | { readonly ok: true; readonly state: GameState; readonly events: readonly GameEvent[] }
  | { readonly ok: false; readonly state: GameState; readonly events: readonly []; readonly reason: RejectReason };

