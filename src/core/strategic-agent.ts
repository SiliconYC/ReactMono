/** P3-13: deterministic policies. Read-only snapshots in; engine commands out. */
import type {GameAction, GameState, Player, ComputerStyle, CardKind, Tile} from './types.js';
import {advancePosition} from './maps.js';
import {loanLimit} from './loan.js';
import {netWorth, propertyVisitAvailable} from './property.js';
import {handSize} from './cards.js';
import {STOCKS, quoteMarket} from './market.js';
import {MAX_BANK_BALANCE} from './money.js';
import {propertyRent, quotePropertyUpgrade} from './property-groups.js';

const POLICIES = {
  conservative: {reserve:650, invest:0.07, mortgageAt:0.20, stockLimit:2},
  balanced: {reserve:320, invest:0.18, mortgageAt:0.25, stockLimit:5},
  aggressive: {reserve:90, invest:0.38, mortgageAt:0.42, stockLimit:10}
} as const;
export const COMPUTER_STYLES: readonly ComputerStyle[]=['conservative','balanced','aggressive'];
export const COMPUTER_STYLE_NAMES:Readonly<Record<ComputerStyle,string>>={
  conservative:'保守',balanced:'平衡',aggressive:'进取'
};
function legalBlock(state:GameState,p:Player,t:Tile):boolean {
  return t.id!==0&&t.id!==p.position&&!state.players.some(x=>!x.bankrupt&&x.position===t.id)
    &&!state.roadblocks?.some(x=>x.tileId===t.id);
}
/** Conservative policy discounts risk; aggressive policy maximizes available opportunity. */
function scoreLanding(state:GameState,p:Player,t:Tile,style:ComputerStyle):number {
  const danger=t.facility==='prison'||t.facility==='hospital'?150:0;
  if(t.kind==='property'&&t.ownerId!==null&&t.ownerId!==p.id) {
    const rent=propertyRent(state,t.id);
    return -rent*(style==='conservative'?4:style==='balanced'?2:1)-danger;
  }
  if(t.kind==='property'&&t.ownerId===null) {
    const price=t.price??0;
    return p.cash-price>=POLICIES[style].reserve ? (t.rent??0)*12-price*(style==='conservative'?0.50:0.20): -price/5;
  }
  if(t.cardStation||t.facility==='shop')return style==='aggressive'?150:90;
  return -danger;
}
function firstOwned(state:GameState,p:Player,test:(t:Tile)=>boolean):Tile|undefined {
  return state.tiles.find(t=>t.kind==='property'&&t.ownerId===p.id&&test(t));
}
function thisTurnEvents(state:GameState,p:Player) {
  let start=-1;
  for(let i=state.events.length-1;i>=0;i--) {
    const e=state.events[i];
    if(e.actorId===p.id&&e.type==='die_rolled'){start=i;break;}
  }
  return state.events.slice(start+1).filter(e=>e.actorId===p.id);
}
export function chooseStyledAction(state:GameState,style:ComputerStyle):GameAction|null {
  if(state.status!=='playing')return null;
  const p=state.players[state.currentPlayerIndex];
  if(!p||p.bankrupt||p.kind!=='computer')return null;
  const cfg=POLICIES[style];
  if(!cfg)throw new Error('电脑策略无效');
  const reserve=Math.min(cfg.reserve+Math.floor(state.players.filter(x=>!x.bankrupt&&x.id!==p.id)
    .reduce((sum,rival)=>sum+Math.max(0,netWorth(state,rival.id)-netWorth(state,p.id)),0)/12),2000);
  const action=(type:GameAction['type']):GameAction=>({type,actorId:p.id} as GameAction);
  switch(state.phase) {
    case 'await_roll': {
      if(p.detention)return action('skip_turn');
      const c=p.cards;
      if((c?.reward??0)>0)return {type:'use_card',actorId:p.id,cardType:'reward'};
      if(state.strategyEnabled&&(c?.remote??0)>0&&(state.pendingDie??0)===0) {
        let best=1,bestScore=-Infinity;
        for(let die=1;die<=6;die++){
          const t=state.tiles[advancePosition(state.map,p.position,die+(state.pendingMoveBonus??0))];
          const value=scoreLanding(state,p,t,style);
          if(value>bestScore){best=die;bestScore=value;}
        }
        return {type:'use_card',actorId:p.id,cardType:'remote',dieValue:best};
      }
      const exposed=state.tiles.some(t=>t.kind==='property'&&t.ownerId&&t.ownerId!==p.id&&
        !t.mortgaged&&Array.from({length:6},(_,i)=>advancePosition(state.map,p.position,i+1))
          .includes(t.id));
      if(state.strategyEnabled&&(c?.rent_free??0)>0&&!state.pendingRentWaiver&&
        (exposed||style==='conservative'))
        return {type:'use_card',actorId:p.id,cardType:'rent_free'};
      if((c?.stride??0)>0&&(state.pendingMoveBonus??0)===0&&
        (style!=='conservative'||!exposed))return {type:'use_card',actorId:p.id,cardType:'stride'};
      if(state.strategyEnabled&&(c?.roadblock??0)>0) {
        // Threats are based on live opponents' positions, never on a benchmark seed.
        const rivals=state.players.filter(x=>!x.bankrupt&&x.id!==p.id)
          .sort((a,b)=>netWorth(state,b.id)-netWorth(state,a.id)||a.id.localeCompare(b.id));
        for(const rival of rivals)for(let step=1;step<=6;step++){
          const t=state.tiles[advancePosition(state.map,rival.position,step)];
          if(legalBlock(state,p,t))return {type:'use_card',actorId:p.id,cardType:'roadblock',tileId:t.id};
        }
      }
      return action('roll');
    }
    case 'await_shop': {
      const shop=state.shops?.find(s=>s.tileId===p.position);
      if(shop&&handSize(p.cards)<(state.cardRules?.maxHand??3)){
        const priorities:readonly CardKind[]=style==='conservative'
          ?['rent_free','reward','remote','stride','roadblock']
          :style==='balanced'?['remote','rent_free','reward','stride','roadblock']
          :['remote','roadblock','stride','reward','rent_free'];
        for(const kind of priorities){
          const price=state.facilityRules?.prices[kind]??Infinity;
          if(shop.cards[kind]>0&&p.cash-price>=reserve)
            return {type:'buy_shop_card',actorId:p.id,cardType:kind};
        }
      }
      return action('leave_shop');
    }
    case 'await_decision': {
      const tile=state.tiles[p.position];
      if(tile.kind!=='property'||tile.ownerId!==null)return null;
      const price=tile.price??0;
      const safe=p.cash-price>=reserve;
      const quality=(tile.rent??0)/Math.max(1,price);
      const buy=style==='conservative'?safe&&quality>=0.15
        :style==='balanced'?safe
        :p.cash>=price&&p.cash-price>=Math.min(35,reserve);
      return action(buy?'buy_property':'decline_property');
    }
    case 'await_end_turn': {
      // One action of each category per actual rolled turn; never deposit/withdraw loops.
      const seen=thisTurnEvents(state,p);
      const did=(...k:string[])=>seen.some(e=>k.includes(e.type));
      const balance=p.bankBalance??0,debt=p.loanBalance??0;
      const available=p.cash+(state.bank?balance:0);
      const purchaseReserve=style==='aggressive'?Math.min(35,reserve):reserve;
      const upgrade=!did('property_upgraded')?firstOwned(state,p,t=>!t.mortgaged&&
        available-(quotePropertyUpgrade(state,t.id)?.cost??Infinity)>=reserve&&
        propertyVisitAvailable(state,p,t.id)):undefined;
      const upgradeCost=upgrade?(quotePropertyUpgrade(state,upgrade.id)?.cost??0):0;
      // 购地阶段不能转账；提前保留一次可承担的购地预算，覆盖遥控骰与加步卡的落点。
      const purchaseCash=state.tiles.reduce((target,t)=>{
        const price=t.price??0,required=price+purchaseReserve;
        return t.kind==='property'&&t.ownerId===null&&available-upgradeCost>=required&&
          (style!=='conservative'||(t.rent??0)/Math.max(1,price)>=0.15)
          ?Math.max(target,required):target;
      },0);
      const operatingCash=upgradeCost+Math.max(purchaseCash,upgrade?reserve:0);
      if(state.loan&&debt>0&&!did('loan_repaid')&&p.cash>reserve+80){
        return {type:'repay_loan',actorId:p.id,amount:Math.min(debt,p.cash-reserve)};
      }
      const withdrawalTarget=Math.max(operatingCash,p.cash<reserve/2?reserve:0);
      if(state.bank&&p.cash<withdrawalTarget&&balance>0&&!did('bank_withdrawn','bank_deposited')){
        return {type:'withdraw_bank',actorId:p.id,amount:Math.min(balance,Math.ceil(withdrawalTarget-p.cash))};
      }
      if(state.market&&p.cash<reserve/2&&!did('stock_sold','stock_liquidated')){
        const holding=STOCKS.find(s=>(p.holdings?.[s.id]?.quantity??0)>0);
        if(holding)return {type:'sell_stock',actorId:p.id,stockId:holding.id,
          quantity:p.holdings![holding.id]!.quantity};
      }
      if(state.loan&&p.cash<reserve*cfg.mortgageAt&&!did('property_mortgaged','loan_borrowed')){
        const tile=firstOwned(state,p,t=>!t.mortgaged);
        if(tile)return {type:'mortgage_property',actorId:p.id,tileId:tile.id};
      }
      const credit=loanLimit(state,p.id)-debt;
      if(state.loan&&credit>0&&p.cash<reserve&&!did('loan_borrowed')){
        return {type:'borrow_loan',actorId:p.id,amount:Math.min(credit,Math.ceil(reserve-p.cash))};
      }
      if(!did('property_upgraded')){
        const tile=firstOwned(state,p,t=>!t.mortgaged&&
          p.cash-(quotePropertyUpgrade(state,t.id)?.cost??Infinity)>=reserve&&
          propertyVisitAvailable(state,p,t.id));
        if(tile)return {type:'upgrade_property',actorId:p.id,tileId:tile.id};
      }
      const stockFunds=state.stockAccount==='bank'?balance:p.cash;
      const stockReserve=state.stockAccount==='bank'?reserve+150:Math.max(reserve+150,operatingCash);
      if(state.market&&!did('stock_bought')&&stockFunds>stockReserve){
        const holdings=STOCKS.reduce((sum,s)=>sum+(p.holdings?.[s.id]?.quantity??0),0);
        if(holdings<cfg.stockLimit){
          const choice=STOCKS.map(s=>({s,price:quoteMarket(state.market!,s.id),
            ratio:quoteMarket(state.market!,s.id)/s.initialPrice}))
            .sort((a,b)=>a.ratio-b.ratio||a.s.id.localeCompare(b.s.id))[0];
          const perShare=choice.price+Math.max(1,Math.ceil(choice.price*0.005));
          const quantity=Math.min(cfg.stockLimit-holdings,
            Math.floor((stockFunds-stockReserve)*cfg.invest/perShare));
          if(quantity>0)return {type:'buy_stock',actorId:p.id,stockId:choice.s.id,quantity};
        }
      }
      if(state.bank&&p.cash>reserve+650&&!did('bank_deposited','bank_withdrawn')){
        const amount=Math.min(1000,MAX_BANK_BALANCE-balance,Math.floor((p.cash-Math.max(reserve+300,operatingCash))/2));
        if(amount>0)return {type:'deposit_bank',actorId:p.id,amount};
      }
      return action('end_turn');
    }
    default:return null;
  }
}
