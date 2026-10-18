/** P3-10: deterministic trades with an optional bank settlement account on the five invented market quotations. */
import type {GameState,Player,GameAction,ActionResult,GameEvent,StockHoldings} from './types.js';
import {quoteMarket,STOCKS} from './market.js';
import {accept,reject} from './transitions.js';
import {MAX_BANK_BALANCE} from './bank.js';
export const STOCK_FEE_BPS=50; // 0.5% each trade, rounded up to one game coin.
export const MAX_SHARES=1_000_000;
export function stockFee(gross:number):number{
  if(!Number.isSafeInteger(gross)||gross<1||gross>MAX_BANK_BALANCE)throw new Error('交易总额无效');
  return Math.max(1,Math.ceil(gross*STOCK_FEE_BPS/10000));
}
export function tradeStock(state:GameState,actor:Player,
  action:Extract<GameAction,{type:'buy_stock'|'sell_stock'}>):ActionResult{
  const quantity=action.quantity;
  if(!state.market||state.phase!=='await_end_turn'||actor.bankrupt||
    !Number.isSafeInteger(quantity)||quantity<1||quantity>MAX_SHARES||
    !STOCKS.some(x=>x.id===action.stockId))return reject(state,'INVALID_PHASE');
  const price=quoteMarket(state.market,action.stockId);
  const gross=price*quantity;
  if(!Number.isSafeInteger(gross)||gross>MAX_BANK_BALANCE)return reject(state,'INVALID_PHASE');
  const fee=stockFee(gross);
  const positions:StockHoldings=actor.holdings??{};
  const lot=positions[action.stockId];
  const account = state.stockAccount === 'bank' ? 'bankBalance' : 'cash';
  let cash=actor[account] ?? 0;
  let next:StockHoldings;
  let event:GameEvent;
  if(action.type==='buy_stock'){
    if(gross+fee>cash)return reject(state,'INSUFFICIENT_FUNDS');
    if((lot?.quantity??0)+quantity>MAX_SHARES||(lot?.costBasis??0)+gross+fee>MAX_BANK_BALANCE)
      return reject(state,'INVALID_PHASE');
    cash-=gross+fee;
    next={...positions,[action.stockId]:{quantity:(lot?.quantity??0)+quantity,
      costBasis:(lot?.costBasis??0)+gross+fee}};
    event={type:'stock_bought',actorId:actor.id,details:{stockId:action.stockId,quantity,price,fee,amount:gross+fee}};
  }else{
    if(!lot||lot.quantity<quantity)return reject(state,'INSUFFICIENT_FUNDS');
    const proceeds=gross-fee;
    if(!Number.isSafeInteger(cash+proceeds)||cash+proceeds>MAX_BANK_BALANCE)
      return reject(state,'INVALID_PHASE');
    const allocated=quantity===lot.quantity?lot.costBasis:Math.floor(lot.costBasis*quantity/lot.quantity);
    const { [action.stockId]:_sold,...others}=positions;
    next=quantity===lot.quantity?others:{...positions,[action.stockId]:{
      quantity:lot.quantity-quantity,costBasis:lot.costBasis-allocated}};
    cash+=proceeds;
    event={type:'stock_sold',actorId:actor.id,details:{stockId:action.stockId,quantity,price,fee,
      amount:proceeds,realized:proceeds-allocated}};
  }
  if(state.stockAccount==='bank')event={...event,details:{...event.details,account:'bank'}};
  return accept(state,[event],{players:state.players.map(p=>p.id===actor.id?{...p,[account]:cash,holdings:next}:p)});
}
/** Pay rent from quoted, fee-adjusted shares before selling land. Full lots only, in fixed symbol order. */
export function liquidateStocksForRent(state:GameState,actor:Player,due:number):{
  cash:number;holdings:StockHoldings|undefined;events:readonly GameEvent[]
}{
  let cash=actor.cash;
  let holdings=actor.holdings;
  const events:GameEvent[]=[];
  if(!state.market||cash>=due)return {cash,holdings,events};
  for(const symbol of STOCKS){
    if(cash>=due)break;
    const lot=holdings?.[symbol.id];
    if(!lot||lot.quantity<1)continue;
    const gross=lot.quantity*quoteMarket(state.market,symbol.id);
    const fee=stockFee(gross);
    const amount=gross-fee;
    if(!Number.isSafeInteger(cash+amount)||cash+amount>MAX_BANK_BALANCE)throw new Error('股票清算超出安全范围');
    cash+=amount;
    const {[symbol.id]:_sold,...others}=holdings!;
    holdings=others;
    events.push({type:'stock_liquidated',actorId:actor.id,details:{stockId:symbol.id,
      quantity:lot.quantity,amount,fee,reason:'rent'}});
  }
  return {cash,holdings,events};
}
