/** P3-01: board defaults and configuration validation. */
import type { GameConfig, FacilityConfig } from './types.js';
export declare const DEFAULT_CARD_RULES: {
    readonly tileIds: readonly [6, 12, 18];
    readonly rewardCash: 80;
    readonly moveBonus: 2;
    readonly maxHand: 3;
};
export declare const DEFAULT_FACILITIES: FacilityConfig;
export declare const DEFAULT_EVENT_RULES: {
    readonly tileIds: readonly [3, 9, 15, 21];
    readonly bonus: 120;
    readonly fee: 60;
};
export declare const DEFAULT_UPGRADES: {
    readonly costRates: readonly [0.5, 0.8];
    readonly rentRates: readonly [1, 2, 4];
};
export declare const DEFAULT_RESALE_RULES: {
    readonly landPercent: 0.75;
    readonly upgradePercent: 0.5;
};
export declare const DEFAULT_CONFIG: GameConfig;
export declare const HARBOR_CONFIG: GameConfig;
export declare function validateConfig(config: GameConfig): void;
