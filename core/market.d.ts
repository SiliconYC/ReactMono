export declare const STOCKS: readonly [{
    readonly id: "SEA";
    readonly name: "海岚科技";
    readonly initialPrice: 80;
}, {
    readonly id: "RIVER";
    readonly name: "碧波航运";
    readonly initialPrice: 130;
}, {
    readonly id: "FARM";
    readonly name: "青禾农业";
    readonly initialPrice: 55;
}, {
    readonly id: "STAR";
    readonly name: "星河能源";
    readonly initialPrice: 105;
}, {
    readonly id: "TOWER";
    readonly name: "远山工业";
    readonly initialPrice: 160;
}];
export type StockId = typeof STOCKS[number]['id'];
export interface StockMarket {
    readonly version: 1;
    readonly round: number;
    /** Independent seeded random sequence; never consumes the dice RNG. */
    readonly rngState: number;
    readonly prices: Readonly<Record<StockId, number>>;
}
export declare function validateMarket(value: unknown): asserts value is StockMarket;
export declare function createMarket(seed: number): StockMarket;
export declare function quoteMarket(market: StockMarket, id: string): number;
/** One fixed settlement per new game round; integer ±6% move per company. */
export declare function advanceMarket(state: StockMarket, round: number): StockMarket;
