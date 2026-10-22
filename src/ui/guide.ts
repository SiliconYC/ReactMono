import type {GameState} from '../core/game.js';
export const GUIDE_STEPS=[
 {title:'认识棋盘',body:'按住地块或房屋可看地价、租金和归属，松手收起；棋子与姓名相对应。'},
 {title:'开始回合',body:'选择地图、人数后开始。轮到你时掷骰，遇到地产再决定买或不买。'},
 {title:'管理资产',body:'掷骰前可办理地产、银行、贷款和股票；出发后只为落点选择暂停，结算完自动交接。'}
] as const;
export function contextHint(game:GameState):string{
 const current=game.players[game.currentPlayerIndex];
 if(game.status==='setup')return '先选地图和玩家人数，再开始；不需要账号。';
 if(game.status==='finished')return '对局已结束：比较净资产，支持立即重新开局。';
 if(current.detention)return '特殊状态：本回合需等待，停留次数按规则递减。';
 if(game.phase==='await_shop')return '商店按显示价格购买道具。手牌满额或现金不足时按钮禁用。';
 if(game.phase==='await_decision')return '可以选择买地或放弃；只有现金够且地产无主才能购买。';
 if(game.phase==='await_end_turn')return '落点有可选建设时请作决定；其他结算完成后自动交接。资产交易请在掷骰前办理。';
 return '掷骰前可以使用已有策略卡；投掷后棋子会沿棋盘路线前进并自动结算租金。';
}
