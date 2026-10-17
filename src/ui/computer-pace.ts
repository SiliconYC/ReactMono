import type {GameAction,GameEvent,GameState} from '../core/game.js';

export type Pace='normal'|'fast';
/** Pure pacing, never participate in action choice or random-state changes. */
export function cpuDelay(pace:Pace,action:GameAction,events:readonly GameEvent[]=[]):number{
 if(pace==='fast')return 12;
 const impactful=events.some(e=>['rent_paid','property_bought','property_upgraded','loan_borrowed',
   'player_bankrupt','facility_entered','game_finished','stock_bought','stock_sold'].includes(e.type));
 if(impactful)return 245;
 if(action.type==='roll'||action.type==='skip_turn')return 200;
 if(action.type==='buy_property'||action.type==='use_card'||action.type==='buy_stock')return 170;
 return 115;
}
export const MAX_CPU_ACTIONS_PER_TURN=48;
export type CpuTiming={readonly decisions:number;readonly calculationMs:number;readonly waitScheduledMs:number;
  readonly lastCalculationMs:number;readonly longCalculationCount:number};
export const initialCpuTiming:CpuTiming={decisions:0,calculationMs:0,waitScheduledMs:0,lastCalculationMs:0,longCalculationCount:0};
export function addCpuTiming(t:CpuTiming,calculationMs:number,nextDelay:number):CpuTiming{
 const ms=Math.max(0,calculationMs);
 return {decisions:t.decisions+1,calculationMs:t.calculationMs+ms,
   waitScheduledMs:t.waitScheduledMs+nextDelay,lastCalculationMs:ms,
   longCalculationCount:t.longCalculationCount+Number(ms>250)};
}
export function cpuTurnKey(state:GameState):string{
 return state.round+':'+state.players[state.currentPlayerIndex]?.id;
}
