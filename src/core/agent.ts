/** 简单、确定性电脑玩家：从只读状态选择合法命令，不直接修改引擎数据。 */
import { type GameAction, type GameState } from './game.js';
import { handSize } from './cards.js';
import {chooseStyledAction} from './strategic-agent.js';
export interface ComputerOptions { readonly reserveCash?: number }
export function choosePhaseAction(state: GameState, reserveCash: number): GameAction | null {
  if (!Number.isFinite(reserveCash) || reserveCash < 0) throw new Error('保留资金必须为非负有限数字');
  if (state.status !== 'playing') return null;
  const player = state.players[state.currentPlayerIndex];
  if (!player) return null;
  switch (state.phase) {
    case 'await_roll': {
      if(player.detention!==undefined)return {type:'skip_turn',actorId:player.id};
      const held=player.cards??{reward:0,stride:0};
      if(held.reward>0)return {type:'use_card',actorId:player.id,cardType:'reward'};
      if(held.stride>0&&(state.pendingMoveBonus??0)===0)return {type:'use_card',actorId:player.id,cardType:'stride'};
      if(state.strategyEnabled===true){
        if((held.remote??0)>0&&(state.pendingDie??0)===0)
          return {type:'use_card',actorId:player.id,cardType:'remote',dieValue:6};
        if((held.rent_free??0)>0&&!state.pendingRentWaiver)
          return {type:'use_card',actorId:player.id,cardType:'rent_free'};
        if((held.roadblock??0)>0){
          const target=state.tiles.find(t=>t.id!==0&&t.id!==player.position&&
            !state.players.some(p=>!p.bankrupt&&p.position===t.id)&&
            !state.roadblocks?.some(b=>b.tileId===t.id));
          if(target)return {type:'use_card',actorId:player.id,cardType:'roadblock',tileId:target.id};
        }
      }
      return {type:'roll',actorId:player.id};
    }
    case 'await_shop': {
      const shop=state.shops?.find(s=>s.tileId===player.position);
      if(shop&&handSize(player.cards)<(state.cardRules?.maxHand??3)){
        for(const cardType of ['remote','roadblock','rent_free','reward','stride'] as const){
          const price=state.facilityRules?.prices[cardType]??Infinity;
          if(shop.cards[cardType]>0&&player.cash>=price+reserveCash)
            return {type:'buy_shop_card',actorId:player.id,cardType};
        }
      }
      return {type:'leave_shop',actorId:player.id};
    }
    case 'await_decision': {
      const tile = state.tiles[player.position];
      if (!tile || tile.kind !== 'property' || tile.ownerId !== null) throw new Error('待购地状态与棋盘数据不一致');
      return { type: player.cash >= (tile.price ?? 0) + reserveCash ? 'buy_property' : 'decline_property', actorId: player.id };
    }
    case 'await_end_turn': {
      const target=state.tiles.find(t=>t.kind==='property'&&t.ownerId===player.id&&
        (t.level??0)<2&&player.cash >= (t.upgradeCosts?.[t.level??0]??Infinity)+reserveCash);
      if(target)return {type:'upgrade_property',actorId:player.id,tileId:target.id};
      // Banking is strictly opt-in; never affect the P2 reference agent.
      if(state.bank && player.cash>3000)return {type:'deposit_bank',actorId:player.id,amount:Math.min(1000,player.cash-1000)};
      if(state.bank && player.cash<100 && (player.bankBalance??0)>0)return {type:'withdraw_bank',actorId:player.id,amount:Math.min(200-player.cash,player.bankBalance??0)};
      return {type:'end_turn',actorId:player.id};
    }
    default: return null;
  }
}
export function chooseComputerAction(state: GameState, options: ComputerOptions = {}): GameAction | null {
  const reserveCash = options.reserveCash ?? 200;
  if (!Number.isFinite(reserveCash) || reserveCash < 0) throw new Error('保留资金必须为非负有限数字');
  const player = state.players[state.currentPlayerIndex];
  if (!player || player.kind !== 'computer') return null;
  return player.computerStyle ? chooseStyledAction(state,player.computerStyle) : choosePhaseAction(state, reserveCash);
}
