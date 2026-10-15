/** 简单、确定性电脑玩家：从只读状态选择合法命令，不直接修改引擎数据。 */
import { type GameAction, type GameState } from './game.js';
export interface ComputerOptions {
    readonly reserveCash?: number;
}
export declare function choosePhaseAction(state: GameState, reserveCash: number): GameAction | null;
export declare function chooseComputerAction(state: GameState, options?: ComputerOptions): GameAction | null;
