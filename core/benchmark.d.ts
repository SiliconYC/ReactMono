import type { ComputerStyle } from './types.js';
export interface StyleScore {
    readonly games: number;
    readonly wins: number;
    readonly bankruptcies: number;
    readonly winRate: number;
    readonly bankruptcyRate: number;
    readonly actionSelection: Readonly<Record<string, number>>;
}
export interface TournamentReport {
    readonly games: number;
    readonly totalActions: number;
    readonly illegalActions: number;
    readonly totalRounds: number;
    readonly averageRounds: number;
    readonly totalTurns: number;
    readonly averageTurns: number;
    readonly byStyle: Readonly<Record<ComputerStyle, StyleScore>>;
    readonly byPlayerCount: Readonly<Record<string, number>>;
    readonly byMap: Readonly<Record<string, number>>;
}
export declare function runStyleBenchmark(games?: number): TournamentReport;
