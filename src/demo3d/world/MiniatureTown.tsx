import { worldForMap } from '../../core/level-data.js';
import { useMemo } from 'react';
import type { GameState, Tile } from '../../core/game.js';
import { rowHouses } from '../properties.js';
import {
  anchorsForMap,
  GROUND_TOP,
  canJoinLots,
  inwardAngleForTile,
  lotForTile,
  ROAD_CONNECTOR_CENTER_Y,
  ROAD_CONNECTOR_THICKNESS,
  ROAD_TILE_CENTER_Y,
  ROAD_TILE_THICKNESS
} from './layout.js';

import { RoadLabels } from './RoadLabels.js';
import { Instances, type Instance } from './Instances.js';
import type { WorldView } from './world-view.js';
type TownProps = Readonly<{ game: GameState; view:WorldView; onSelectTile?: (tileId:number)=>void }>;

import { MASCOT_SEAT_COLORS as PLAYER_COLORS } from './seats.js';
function colorForOwner(game: GameState, ownerId: string): string {
  const index = game.players.findIndex(player => player.id === ownerId);
  return PLAYER_COLORS[index] ?? '#f8c95d';
}

function House({ tile, game }: { tile: Tile; game: GameState }): React.JSX.Element {
  const owner = tile.ownerId === null ? null : colorForOwner(game, tile.ownerId);
  if (owner === null || (tile.level ?? 0) === 0) {
    return (
      <group>
        <mesh position={[0, 0.08, 0]}>
          <boxGeometry args={[1.05, 0.16, 1.05]} />
          <meshStandardMaterial color={owner ?? "#c5d79a"} roughness={0.92} />
        </mesh>
        {[-0.38, 0.38].map(x => [-0.38, 0.38].map(z => (
          <mesh key={`${x}-${z}`} position={[x, 0.24, z]}>
            <cylinderGeometry args={[0.035, 0.045, 0.38, 6]} />
            <meshStandardMaterial color="#e7f0c6" roughness={0.9} />
          </mesh>
        )))}
      </group>
    );
  }
  const level = tile.level ?? 0;
  const height = 0.85 + (level - 1) * 0.6;
  return (
    <group>
      <mesh position={[0, 0.09, 0]}>
        <boxGeometry args={[1.18, 0.18, 1.18]} />
        <meshStandardMaterial color={owner} roughness={0.82} />
      </mesh>
      <mesh position={[0, height / 2 + 0.16, 0]}>
        <boxGeometry args={[0.82, height, 0.76]} />
        <meshStandardMaterial color={owner === '#ff715b' ? '#ffb278' : owner === '#4f7cff' ? '#91b5ff' : owner} roughness={0.78} />
      </mesh>
      <mesh position={[0, height + 0.42, 0]} rotation={[0, Math.PI / 4, 0]}>
        <coneGeometry args={[0.69, 0.5, 4]} />
        <meshStandardMaterial color={owner === '#ff715b' ? '#c85045' : owner === '#4f7cff' ? '#385da9' : owner} roughness={0.72} />
      </mesh>
      <mesh position={[0, 0.42, 0.39]}>
        <boxGeometry args={[0.2, 0.38, 0.03]} />
        <meshStandardMaterial color="#22504c" roughness={0.7} />
      </mesh>
      {[-0.23, 0.23].map(x => (
        <mesh key={x} position={[x, 0.65 + level * 0.12, 0.395]}>
          <boxGeometry args={[0.18, 0.2, 0.025]} />
          <meshStandardMaterial color="#fff0ae" emissive="#ffc45d" emissiveIntensity={0.2} />
        </mesh>
      ))}
      <group position={[0.55, 0.74, 0]}>
        <mesh position={[0, -0.28, 0]}>
          <cylinderGeometry args={[0.025, 0.025, 0.7, 6]} />
          <meshStandardMaterial color="#335e58" />
        </mesh>
        <mesh position={[0.16, 0, 0]}>
          <boxGeometry args={[0.32, 0.2, 0.035]} />
          <meshStandardMaterial color={owner} roughness={0.75} />
        </mesh>
      </group>
    </group>
  );
}

export function MiniatureTown({ game, view, onSelectTile }: TownProps): React.JSX.Element {
  const anchors = anchorsForMap(game.map);
  const detail=view.zoom>=17;
  const visible=(p:{x:number;z:number})=>p.x>=view.minX&&p.x<=view.maxX&&p.z>=view.minZ&&p.z<=view.maxZ;
  const roads=useMemo(()=>anchors.tiles.map((p,id)=>({...p,y:ROAD_TILE_CENTER_Y,rotation:worldForMap(game.map)?.tiles[id].rotation??0,color:id===0?'#e8b84c':game.tiles[id].kind==='property'?'#f0ebd8':'#c9dcd4'})),[anchors,game.map]);
  const edges=useMemo(()=>game.map.route.map((id,i)=>{
    const a=anchors.tiles[id],b=anchors.tiles[game.map.route[(i+1)%game.map.route.length]];
    return {x:(a.x+b.x)/2,y:ROAD_CONNECTOR_CENTER_Y,z:(a.z+b.z)/2,sx:.72,sz:Math.hypot(a.x-b.x,a.z-b.z),rotation:Math.atan2(b.x-a.x,b.z-a.z)};
  }),[anchors,game.map]);
  const lots=useMemo(()=>game.tiles.map(tile=>({...anchors.lots[tile.id],y:GROUND_TOP+.035,rotation:inwardAngleForTile(tile.id,game.map),color:tile.ownerId?colorForOwner(game,tile.ownerId):tile.kind==='property'?'#d2d8b3':'#9fbe91'})),[game.tiles,anchors,game.players]);
  const posts:Instance[]=detail?lots.filter(visible).flatMap(p=>[-.43,.43].map(x=>({x:p.x+Math.cos(p.rotation)*x,z:p.z-Math.sin(p.rotation)*x,y:GROUND_TOP+.15,color:p.color}))):[];
  const simpleHouses=game.tiles.filter(t=>t.ownerId&&(t.level??0)>0&&!detail).map(t=>({...anchors.lots[t.id],y:GROUND_TOP+.5,sy:1+(t.level??1)*.3,color:colorForOwner(game,t.ownerId!)}));
  return (
    <group name="路线与街区">
      <RoadLabels map={game.map} view={view}/>
      <Instances items={edges}><boxGeometry args={[1,ROAD_CONNECTOR_THICKNESS,1]}/><meshStandardMaterial color="#d7d7bd" roughness={1}/></Instances>
      <Instances items={roads} onSelect={onSelectTile}><boxGeometry args={[1.78,ROAD_TILE_THICKNESS,1.78]}/><meshStandardMaterial roughness={.94}/></Instances>
      <Instances items={lots}><boxGeometry args={[1.18,.07,1.18]}/><meshStandardMaterial roughness={1}/></Instances>
      <Instances items={posts}><cylinderGeometry args={[.035,.045,.3,5]}/><meshStandardMaterial roughness={1}/></Instances>
      <Instances items={simpleHouses}><boxGeometry args={[.78,.8,.78]}/><meshStandardMaterial roughness={.9}/></Instances>
      {detail&&game.tiles.filter(tile=>visible(anchors.lots[tile.id])).map(tile => {
        const lot = lotForTile(tile.id, game.map);
        const angle = inwardAngleForTile(tile.id, game.map);
        if(tile.kind!=='property'||(tile.level??0)===0)return null;
        return (
          <group key={tile.id} position={[lot.x, GROUND_TOP, lot.z]} rotation={[0, angle, 0]}>
            <House tile={tile} game={game} />
          </group>
        );
      })}

      {/* Shared walls and roof strips visibly join only eligible street neighbours. */}
      {rowHouses(game).flatMap(row => row.tileIds.slice(1).map((id, index) => {
        if(!detail||!canJoinLots(row.tileIds[index],id,game.map)||!visible(anchors.lots[id]))return null;
        const a = lotForTile(row.tileIds[index], game.map);
        const b = lotForTile(id, game.map);
        const horizontal = a.z === b.z;
        const height = Math.min(game.tiles[id].level ?? 1, game.tiles[row.tileIds[index]].level ?? 1) === 2 ? 1.45 : 0.85;
        return (
          <group key={`terrace-${id}`} position={[(a.x + b.x) / 2, GROUND_TOP, (a.z + b.z) / 2]}>
            <mesh position={[0, 0.09, 0]}>
              <boxGeometry args={horizontal ? [1.35, 0.18, 0.86] : [0.86, 0.18, 1.35]} />
              <meshStandardMaterial color={colorForOwner(game, row.ownerId)} roughness={0.86} />
            </mesh>
            <mesh position={[0, height / 2 + 0.18, 0]}>
              <boxGeometry args={horizontal ? [1.22, height, 0.72] : [0.72, height, 1.22]} />
              <meshStandardMaterial color={row.ownerId === game.players[0]?.id ? '#ffb278' : row.ownerId === game.players[1]?.id ? '#91b5ff' : colorForOwner(game, row.ownerId)} roughness={0.78} />
            </mesh>
            <mesh position={[0, height + 0.25, 0]}>
              <boxGeometry args={horizontal ? [1.35, 0.18, 0.86] : [0.86, 0.18, 1.35]} />
              <meshStandardMaterial color={row.ownerId === game.players[0]?.id ? '#c85045' : row.ownerId === game.players[1]?.id ? '#385da9' : colorForOwner(game, row.ownerId)} />
            </mesh>
          </group>
        );
      }))}

    </group>
  );
}

