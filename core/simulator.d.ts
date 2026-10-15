/** 真实引擎无界面完整对局；记录种子与每一步，拒绝循环或伪造终局。 */
import { type GameConfig, type GameState } from './game.js';
export interface SimulationOptions {
    readonly config?: GameConfig;
    readonly reserveCash?: number;
    readonly humanReserveCash?: number;
    readonly maxActions?: number;
}
export interface SimulationReport {
    readonly seed: number;
    readonly finalState: GameState;
    readonly playerTurns: number;
    readonly actions: number;
    readonly rejections: number;
    readonly finishReason: string;
    readonly trace: readonly string[];
}
export declare function runSimulation(seed: number, options?: SimulationOptions): SimulationReport;
