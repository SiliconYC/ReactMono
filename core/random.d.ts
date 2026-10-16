/** P3-01: deterministic PRNG; never use Math.random for game rules. */
/** 固定 32 位种子，避免 Math.random 导致的回放不一致。 */
export declare function normalizeSeed(seed: number): number;
/** 返回新随机状态；绝不修改传入状态。 */
export declare function nextDie(randomState: number): {
    readonly value: number;
    readonly nextState: number;
};
