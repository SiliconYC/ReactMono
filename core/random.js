/** P3-01: deterministic PRNG; never use Math.random for game rules. */
/** 固定 32 位种子，避免 Math.random 导致的回放不一致。 */
export function normalizeSeed(seed) {
    if (!Number.isFinite(seed))
        throw new Error('随机种子必须是有限数字');
    return (Math.trunc(seed) >>> 0) || 0x6d2b79f5;
}
/** 返回新随机状态；绝不修改传入状态。 */
export function nextDie(randomState) {
    let x = normalizeSeed(randomState);
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    const nextState = x >>> 0;
    return { value: 1 + (nextState % 6), nextState };
}
