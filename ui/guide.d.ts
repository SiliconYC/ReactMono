import type { GameState } from '../core/game.js';
export declare const GUIDE_STEPS: readonly [{
    readonly title: "认识棋盘";
    readonly body: "点击格子可看地价、租金和归属；棋子与姓名相对应。";
}, {
    readonly title: "开始回合";
    readonly body: "选择地图、人数后开始。轮到你时掷骰，遇到地产再决定买或不买。";
}, {
    readonly title: "管理资产";
    readonly body: "掷骰后，可按需展开地产、银行、贷款、股票；结束回合交给下一位。";
}];
export declare function contextHint(game: GameState): string;
