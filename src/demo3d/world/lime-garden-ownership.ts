import { Color, SRGBColorSpace } from 'three';
import type { GameState } from '../../core/game.js';
import { MASCOT_SEAT_COLORS } from './seats.js';

export function gardenOwnerColor(game:Pick<GameState,'players'>,ownerId:string|null|undefined):string {
  return MASCOT_SEAT_COLORS[game.players.findIndex(player=>player.id===ownerId)]??'#f5df9e';
}

export function gardenRoadColor(game:Pick<GameState,'players'|'tiles'>,tileId:number,selected:boolean):string {
  const tile=game.tiles[tileId];
  const base=selected?'#fff3b8':tile.kind==='property'?'#fff0ce':tileId===0?'#ffe1a7':'#e8efce';
  if(!tile.ownerId)return base;
  return '#'+new Color(base).lerp(new Color(gardenOwnerColor(game,tile.ownerId)),selected?.14:.22).getHexString();
}

export function gardenBuildingOwnerColor(game:Pick<GameState,'players'>,ownerId:string|null|undefined):string {
  if(!game.players.some(player=>player.id===ownerId))return '#b3aea5';
  const color=new Color(gardenOwnerColor(game,ownerId)),hsl=color.getHSL({h:0,s:0,l:0},SRGBColorSpace);
  return '#'+color.setHSL(hsl.h,Math.max(.8,hsl.s),Math.min(.56,hsl.l),SRGBColorSpace).getHexString();
}
