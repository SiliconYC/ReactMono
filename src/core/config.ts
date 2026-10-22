/** P3-01: board defaults and configuration validation. */
import type { GameConfig, FacilityConfig } from './types.js';
import { inferMap, validateMap } from './maps.js';
import { levelConfig } from './level-data.js';
export const DEFAULT_CARD_RULES = { tileIds:[6,12,18], rewardCash:80, moveBonus:2, maxHand:3 } as const;
export const DEFAULT_FACILITIES:FacilityConfig={
  hospitalTiles:[3],prisonTiles:[9],shopTiles:[12],
  hospitalTurns:2,prisonTurns:3,hospitalFee:50,prisonFee:80,
  prices:{reward:120,stride:110,remote:210,roadblock:180,rent_free:160},
  stock:{reward:2,stride:2,remote:2,roadblock:2,rent_free:2}
};
export const DEFAULT_EVENT_RULES = { tileIds:[3,9,15,21], bonus:120, fee:60 } as const;
export const DEFAULT_UPGRADES = { costRates: [0.5, 0.8], rentRates: [1, 2, 4] } as const;
export const DEFAULT_RESALE_RULES = {landPercent:0.75,upgradePercent:0.5} as const;
/** Stable IDs preserve the original maps, prices and saved-game contracts. */
// Preserve the legacy shorthand: replacing tiles without a map still infers a tiny fixture board.
const {map: _classicMap, eventRules: _classicEvents, cardRules: _classicCards, facilityConfig: _classicFacilities, ...classicConfig} = levelConfig('classic-24');
export const DEFAULT_CONFIG: GameConfig = classicConfig;
export const HARBOR_CONFIG: GameConfig = levelConfig('harbor-20');

export function validateConfig(config: GameConfig): void {
  if(config.endCondition!==undefined && config.endCondition!=='bankruptcy')throw new Error('结束条件无效');
  if(config.propertyVisitOnly!==undefined && typeof config.propertyVisitOnly!=='boolean')throw new Error('地产到访规则无效');
  if(config.stockAccount!==undefined && !['cash','bank'].includes(config.stockAccount))throw new Error('股票结算账户无效');
  if(config.stockAccount==='bank' && (config.bankEnabled!==true || config.marketEnabled!==true))throw new Error('存款股票交易需要银行和股市');
  if(config.strategyEnabled!==undefined&&typeof config.strategyEnabled!=='boolean')throw new Error('策略卡开关无效');
  if(config.specialEnabled!==undefined&&typeof config.specialEnabled!=='boolean')throw new Error('特殊设施开关无效');
  if(config.specialEnabled===true&&config.strategyEnabled!==true)throw new Error('特殊设施依赖策略卡');
  if(config.loanEnabled!==undefined&&typeof config.loanEnabled!=='boolean')throw new Error('贷款开关无效');
  if(config.loanEnabled===true&&config.bankEnabled!==true)throw new Error('贷款需要银行模块');
  if(config.loanInterestBps!==undefined&&(!Number.isSafeInteger(config.loanInterestBps)||config.loanInterestBps<0||config.loanInterestBps>1000))throw new Error('贷款利率无效');
  if(config.bankEnabled!==undefined&&typeof config.bankEnabled!=='boolean')throw new Error('银行开关无效');
  if(config.bankInterestBps!==undefined&&(!Number.isSafeInteger(config.bankInterestBps)||config.bankInterestBps<0||config.bankInterestBps>1000))throw new Error('银行利率无效');
  if (config.players.length < 2 || config.players.length > 4 ||
      new Set(config.players.map(p => p.id)).size !== config.players.length ||
      config.players.some(p => !p.id?.trim() || !p.name?.trim() ||
        (p.kind !== undefined && p.kind !== 'human' && p.kind !== 'computer') ||
        (p.computerStyle!==undefined && ((p.kind??'computer')!=='computer' ||
          !['conservative','balanced','aggressive'].includes(p.computerStyle)))))
    throw new Error('玩家配置必须包含两至四名合法且不同的玩家');
  if (config.tiles.length < 2 || config.tiles[0]?.kind !== 'start' ||
      config.tiles.filter(t => t.kind === 'start').length !== 1 ||
      config.tiles.some((t, i) => t.id !== i || !t.title.trim())) throw new Error('地图配置无效');
  validateMap(config.map??inferMap(config.tiles.length),config.tiles.length);
  if(config.terraceRulesVersion!==undefined&&(config.terraceRulesVersion!==1||config.map?.id!=='lime-garden-30'))throw new Error('联排规则只适用于青柠游园');
  if(config.specialEnabled===true){
    const f=config.facilityConfig??DEFAULT_FACILITIES;
    const ids=[...f.hospitalTiles,...f.prisonTiles,...f.shopTiles];
    if(new Set(ids).size!==ids.length||f.hospitalTiles.length<1||f.prisonTiles.length<1||f.shopTiles.length<1||
       ids.some(i=>!Number.isInteger(i)||i<=0||i>=config.tiles.length||config.tiles[i].kind!=='neutral')||
       ![f.hospitalTurns,f.prisonTurns].every(n=>Number.isSafeInteger(n)&&n>=1&&n<=20)||
       ![f.hospitalFee,f.prisonFee].every(n=>Number.isSafeInteger(n)&&n>=0&&n<=1_000_000)||
       !['reward','stride','remote','roadblock','rent_free'].every(k=>
         Number.isSafeInteger(f.prices[k as keyof typeof f.prices])&&f.prices[k as keyof typeof f.prices]>0&&
         f.prices[k as keyof typeof f.prices]<=1_000_000&&
         Number.isSafeInteger(f.stock[k as keyof typeof f.stock])&&f.stock[k as keyof typeof f.stock]>=0&&
         f.stock[k as keyof typeof f.stock]<=100))
       throw new Error('医院、监狱或商店配置无效');
  }
  if (!Number.isFinite(config.initialCash) || config.initialCash < 0 ||
      !Number.isInteger(config.maxRounds) || config.maxRounds < 1) throw new Error('游戏经济配置无效');
  const cards=config.cardRules??DEFAULT_CARD_RULES;
  if(![cards.rewardCash,cards.moveBonus,cards.maxHand].every(x=>Number.isSafeInteger(x)&&x>0)||
    new Set(cards.tileIds).size!==cards.tileIds.length||
    cards.tileIds.some(i=>!Number.isInteger(i)||i<0||(i<config.tiles.length&&config.tiles[i].kind!=='neutral')))
    throw new Error('卡片配置无效');
  const ev=config.eventRules??DEFAULT_EVENT_RULES;
  if(![ev.bonus,ev.fee].every(v=>Number.isSafeInteger(v)&&v>=0)||
    new Set(ev.tileIds).size!==ev.tileIds.length||
    ev.tileIds.some(i=>!Number.isInteger(i)||i<0||(i<config.tiles.length&&config.tiles[i].kind!=='neutral')))
    throw new Error('随机事件配置无效');
  const resale=config.resaleRules??DEFAULT_RESALE_RULES;
  if(![resale.landPercent,resale.upgradePercent].every(x=>Number.isFinite(x)&&x>=0&&x<=1))throw new Error('地产出售折价比例无效');
  const up=config.upgrades ?? DEFAULT_UPGRADES;
  if(up.costRates.length!==2 || up.rentRates.length!==3 ||
    ![...up.costRates,...up.rentRates].every(x=>Number.isFinite(x)&&x>=0) ||
    up.rentRates[0]!==1) throw new Error('地产升级倍率配置无效');
  if (config.tiles.some(t => t.kind === 'property' &&
      (!Number.isFinite(t.price) || (t.price ?? 0) < 0 || !Number.isFinite(t.rent) || (t.rent ?? 0) < 0))) {
    throw new Error('地产价格或租金无效');
  }
}

