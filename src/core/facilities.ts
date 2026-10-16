/** Pure finite-state rules for hospitals, prisons and inventory-limited shops. */
import type {GameState,Player,GameAction,ActionResult,GameEvent,CardKind} from './types.js';
import {accept,reject} from './transitions.js';
import {endTurn} from './turns.js';
import {handSize} from './cards.js';
const KINDS:readonly CardKind[]=['reward','stride','remote','roadblock','rent_free'];
export function buyShopCard(state:GameState,actor:Player,action:Extract<GameAction,{type:'buy_shop_card'}>):ActionResult{
  if(state.phase!=='await_shop'||state.specialEnabled!==true||
     state.tiles[actor.position]?.facility!=='shop'||!KINDS.includes(action.cardType)||
     actor.detention!==undefined)return reject(state,'INVALID_PHASE');
  const shop=state.shops?.find(s=>s.tileId===actor.position);
  const price=state.facilityRules?.prices[action.cardType];
  if(!shop||price===undefined||!Number.isSafeInteger(price)||price<=0||
     shop.cards[action.cardType]<1||handSize(actor.cards)>=(state.cardRules?.maxHand??3))
    return reject(state,'INVALID_PHASE');
  if(actor.cash<price)return reject(state,'INSUFFICIENT_FUNDS');
  return accept(state,[{type:'shop_purchased',actorId:actor.id,details:{
    tileId:shop.tileId,cardType:action.cardType,amount:price}}],{
    players:state.players.map(p=>p.id===actor.id?{...p,cash:p.cash-price,
      cards:{reward:p.cards?.reward??0,stride:p.cards?.stride??0,...p.cards,
        [action.cardType]:(p.cards?.[action.cardType]??0)+1}}:p),
    shops:state.shops!.map(s=>s.tileId===shop.tileId?{...s,
      cards:{...s.cards,[action.cardType]:s.cards[action.cardType]-1}}:s)
  });
}
export function leaveShop(state:GameState,actor:Player):ActionResult{
  if(state.phase!=='await_shop'||state.tiles[actor.position]?.facility!=='shop')
    return reject(state,'INVALID_PHASE');
  return accept(state,[{type:'shop_left',actorId:actor.id,details:{tileId:actor.position}}],{phase:'await_end_turn'});
}
/** Skips only the current detained player's turn; no dice draw or property event. */
export function skipDetentionTurn(state:GameState,actor:Player):ActionResult{
  if(state.phase!=='await_roll'||!actor.detention||actor.detention.remaining<1)
    return reject(state,'INVALID_PHASE');
  const remaining=actor.detention.remaining-1;
  const players=state.players.map(p=>{
    if(p.id!==actor.id)return p;
    const {detention:_old,...rest}=p;
    return remaining>0?{...rest,detention:{...actor.detention!,remaining}}:rest;
  });
  const ended=endTurn({...state,phase:'await_end_turn',players},actor);
  if(!ended.ok)return reject(state,'INVALID_PHASE');
  const extra:GameEvent[]=[{type:'detention_skipped',actorId:actor.id,
    details:{kind:actor.detention.kind,remaining}}];
  if(remaining===0)extra.push({type:'detention_released',actorId:actor.id,details:{kind:actor.detention.kind}});
  const events=[...extra,...ended.events];
  return {ok:true,events,state:{...ended.state,events:[...state.events,...events]}};
}
