/** P3-08: deterministic secured loans. The bank is a virtual lender, never another player. */
import type { GameState, Player, Tile, GameAction, ActionResult, GameEvent, LoanState } from './types.js';
import { resaleValue } from './property.js';
import { accept, reject } from './transitions.js';
import { MAX_BANK_BALANCE } from './bank.js';

export const DEFAULT_LOAN_INTEREST_BPS=200; // 2% per complete game round
export function createLoan(interestBps=DEFAULT_LOAN_INTEREST_BPS):LoanState {
  if(!Number.isSafeInteger(interestBps)||interestBps<0||interestBps>1000)throw new Error('贷款利率无效');
  return {version:1,interestBps,lastInterestRound:1};
}
export function loanLimit(state:GameState,playerId:string,excludeId:number=-1):number{
  if(!state.loan)return 0;
  return state.tiles.reduce((sum,t)=>sum+(t.kind==='property'&&t.ownerId===playerId&&t.mortgaged===true&&t.id!==excludeId
    ? Math.floor(resaleValue(t,state.resaleRules)/2):0),0);
}
export function transferLoan(state:GameState,actor:Player,action:Extract<GameAction,
  {type:'mortgage_property'|'release_mortgage'|'borrow_loan'|'repay_loan'}>):ActionResult {
  if(!state.loan||state.phase!=='await_end_turn'||actor.bankrupt)return reject(state,'INVALID_PHASE');
  if(action.type==='mortgage_property'||action.type==='release_mortgage'){
    if(!Number.isSafeInteger(action.tileId))return reject(state,'INVALID_PHASE');
    const tile=state.tiles[action.tileId];
    if(!tile||tile.kind!=='property'||tile.ownerId!==actor.id)return reject(state,'INVALID_PHASE');
    if(action.type==='mortgage_property'){
      if(tile.mortgaged===true||loanLimit(state,actor.id)+Math.floor(resaleValue(tile,state.resaleRules)/2)>MAX_BANK_BALANCE)
        return reject(state,'INVALID_PHASE');
      return accept(state,[{type:'property_mortgaged',actorId:actor.id,details:{tileId:tile.id,credit:Math.floor(resaleValue(tile,state.resaleRules)/2)}}],{
        tiles:state.tiles.map(t=>t.id===tile.id?{...t,mortgaged:true}:t)
      });
    }
    if(tile.mortgaged!==true||(actor.loanBalance??0)>loanLimit(state,actor.id,tile.id))
      return reject(state,'INVALID_PHASE');
    return accept(state,[{type:'property_released',actorId:actor.id,details:{tileId:tile.id}}],{
      tiles:state.tiles.map(t=>t.id===tile.id?(({mortgaged:_unused,...rest})=>rest)(t):t)
    });
  }
  const amount=action.amount,old=actor.loanBalance??0;
  if(!Number.isSafeInteger(amount)||amount<1||amount>MAX_BANK_BALANCE)
    return reject(state,'INVALID_PHASE');
  if(action.type==='borrow_loan'){
    if(amount>loanLimit(state,actor.id)-old||actor.cash+amount>MAX_BANK_BALANCE)
      return reject(state,'INSUFFICIENT_FUNDS');
    return accept(state,[{type:'loan_borrowed',actorId:actor.id,details:{amount}}],{
      players:state.players.map(p=>p.id===actor.id?{...p,cash:p.cash+amount,loanBalance:old+amount}:p)
    });
  }
  if(amount>old||amount>actor.cash)return reject(state,'INSUFFICIENT_FUNDS');
  return accept(state,[{type:'loan_repaid',actorId:actor.id,details:{amount}}],{
    players:state.players.map(p=>p.id===actor.id?{...p,cash:p.cash-amount,loanBalance:old-amount}:p)
  });
}
/** Compounding is only allowed while collateral covers it. Otherwise the lender seizes pledged land.
 * Pledged collateral's resale value repays principal and excess proceeds return to the borrower.
 * Deficiency is recorded as a bank loss (not shifted to another player).
 */
export function foreclose(state:GameState,player:Player,tiles:readonly Tile[]):{
  player:Player;tiles:readonly Tile[];events:readonly GameEvent[]
}{
  const pledged=tiles.filter(t=>t.ownerId===player.id&&t.kind==='property'&&t.mortgaged===true);
  const recovered=pledged.reduce((sum,t)=>sum+resaleValue(t,state.resaleRules),0);
  const debt=player.loanBalance??0;
  const events:GameEvent[]=debt>0?[{type:'loan_default',actorId:player.id,details:{
    debt,recovered:Math.min(recovered,debt),writtenOff:Math.max(0,debt-recovered),
    collateral:pledged.length
  }}]:[];
  return {player:{...player,cash:player.cash+Math.max(0,recovered-debt),loanBalance:0},
    tiles:tiles.map(t=>pledged.some(x=>x.id===t.id)?(({mortgaged:_unused,...rest})=>({...rest,ownerId:null,level:0}))(t):t),
    events};
}
export function settleLoanRound(state:GameState,players:readonly Player[],tiles:readonly Tile[],round:number):{
  loan:LoanState;players:readonly Player[];tiles:readonly Tile[];events:readonly GameEvent[]
}{
  if(!state.loan||!Number.isSafeInteger(round)||round!==state.loan.lastInterestRound+1)
    throw new Error('贷款重复结息或轮次跳跃');
  let currentTiles=tiles;
  const events:GameEvent[]=[];
  const settled=players.map(p=>{
    const old=p.loanBalance??0;
    if(p.bankrupt||old===0)return p;
    const interest=Math.ceil(old*state.loan!.interestBps/10000);
    const fromCash=Math.min(interest,p.cash);
    const fromBank=Math.min(interest-fromCash,p.bankBalance??0);
    const remaining=interest-fromCash-fromBank;
    if(remaining>MAX_BANK_BALANCE-old)throw new Error('贷款超过安全范围');
    let result:Player={...p,cash:p.cash-fromCash,
      bankBalance:(p.bankBalance??0)-fromBank,loanBalance:old+remaining};
    if(fromBank>0)events.push({type:'bank_withdrawn',actorId:p.id,details:{amount:fromBank,reason:'loan_interest'}});
    if(interest>0)events.push({type:'loan_interest',actorId:p.id,details:{round,amount:interest,paid:fromCash+fromBank,capitalized:remaining}});
    if(result.loanBalance!>loanLimit({...state,tiles:currentTiles},p.id)){
      const seized=foreclose(state,result,currentTiles);
      result=seized.player;currentTiles=seized.tiles;events.push(...seized.events);
    }
    return result;
  });
  return {loan:{...state.loan,lastInterestRound:round},players:settled,tiles:currentTiles,events};
}
