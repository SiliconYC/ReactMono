/** Card actions are deterministic and may only be invoked by the active player. */
import type { GameState, Player, GameAction, ActionResult } from './types.js';
import { DEFAULT_CARD_RULES } from './config.js';
import { accept, reject } from './transitions.js';
export function useCard(state: GameState, actor: Player, action: Extract<GameAction,{type:'use_card'}>): ActionResult {
      if(state.phase!=='await_roll'||(action.targetId!==undefined&&action.targetId!==actor.id)||
        !['reward','stride'].includes(action.cardType))return reject(state,'INVALID_PHASE');
      const held=actor.cards??{reward:0,stride:0};
      if((held[action.cardType]??0)<1||(action.cardType==='stride'&&(state.pendingMoveBonus??0)>0))return reject(state,'INVALID_PHASE');
      const rules=state.cardRules??DEFAULT_CARD_RULES;
      const reward=action.cardType==='reward'?rules.rewardCash:0;
      return accept(state,[{type:'card_used',actorId:actor.id,details:{cardType:action.cardType,amount:reward,moveBonus:action.cardType==='stride'?rules.moveBonus:0}}],{
        players:state.players.map(p=>p.id===actor.id?{...p,cash:p.cash+reward,cards:{...held,[action.cardType]:held[action.cardType]-1}}:p),
        pendingMoveBonus:action.cardType==='stride'?rules.moveBonus:(state.pendingMoveBonus??0)
      });
}
