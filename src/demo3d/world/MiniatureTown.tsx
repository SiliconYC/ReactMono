import * as THREE from 'three';
import { useEffect, useMemo } from 'react';
import type { GameState, Tile } from '../../core/game.js';
import { rowHouses } from '../properties.js';
import { LOT_ANCHORS, TILE_ANCHORS } from './layout.js';

type TownProps = Readonly<{ game: GameState }>;

const OWNER_COLORS: Readonly<Record<string, string>> = { p1: '#ff715b', p2: '#4f7cff' };

function Tree({ position, scale = 1 }: { position: [number, number, number]; scale?: number }): React.JSX.Element {
  return (
    <group position={position} scale={scale}>
      <mesh position={[0, 0.34, 0]}>
        <cylinderGeometry args={[0.1, 0.15, 0.68, 7]} />
        <meshStandardMaterial color="#8f6546" roughness={0.9} />
      </mesh>
      <mesh position={[0, 0.92, 0]}>
        <dodecahedronGeometry args={[0.45, 0]} />
        <meshStandardMaterial color="#4d9d72" roughness={0.9} />
      </mesh>
      <mesh position={[-0.2, 0.84, 0.1]}>
        <dodecahedronGeometry args={[0.28, 0]} />
        <meshStandardMaterial color="#6fbf85" roughness={0.9} />
      </mesh>
    </group>
  );
}

function Lamp({ position }: { position: [number, number, number] }): React.JSX.Element {
  return (
    <group position={position}>
      <mesh position={[0, 0.45, 0]}>
        <cylinderGeometry args={[0.035, 0.055, 0.9, 8]} />
        <meshStandardMaterial color="#29534f" roughness={0.7} />
      </mesh>
      <mesh position={[0, 0.91, 0]}>
        <octahedronGeometry args={[0.13, 0]} />
        <meshStandardMaterial color="#ffe7a3" emissive="#f4b85d" emissiveIntensity={0.45} roughness={0.5} />
      </mesh>
    </group>
  );
}

function House({ tile }: { tile: Tile }): React.JSX.Element {
  const owner = tile.ownerId === null ? null : OWNER_COLORS[tile.ownerId] ?? '#f8c95d';
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
        <meshStandardMaterial color={tile.ownerId === 'p1' ? '#ffb278' : '#91b5ff'} roughness={0.78} />
      </mesh>
      <mesh position={[0, height + 0.42, 0]} rotation={[0, Math.PI / 4, 0]}>
        <coneGeometry args={[0.69, 0.5, 4]} />
        <meshStandardMaterial color={tile.ownerId === 'p1' ? '#c85045' : '#385da9'} roughness={0.72} />
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

function BankBuilding(): React.JSX.Element {
  const sign = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 256; canvas.height = 80;
    const context = canvas.getContext('2d');
    if (context) {
      context.fillStyle = '#24594f'; context.fillRect(0, 0, 256, 80);
      context.fillStyle = '#ffe39b'; context.font = 'bold 45px "PingFang SC", "Microsoft YaHei", sans-serif';
      context.textAlign = 'center'; context.textBaseline = 'middle'; context.fillText('晴湾银行', 128, 42);
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }, []);
  useEffect(() => () => sign.dispose(), [sign]);
  return (
    <group name="晴湾银行">
      <mesh position={[0, 0.05, 0]}><cylinderGeometry args={[1.05, 1.12, 0.2, 8]} /><meshStandardMaterial color="#c1d3c4" /></mesh>
      <mesh position={[0, 0.65, -0.05]}><boxGeometry args={[1.24, 1.05, 0.96]} /><meshStandardMaterial color="#fff2ce" /></mesh>
      <mesh position={[0, 1.23, 0]}><boxGeometry args={[1.48, 0.18, 1.15]} /><meshStandardMaterial color="#427f73" /></mesh>
      <mesh position={[0, 0.54, 0.455]}><boxGeometry args={[0.3, 0.72, 0.035]} /><meshStandardMaterial color="#3a7165" /></mesh>
      {[-0.5, 0.5].map(x => <mesh key={x} position={[x, 0.68, 0.55]}><cylinderGeometry args={[0.075, 0.09, 0.92, 8]} /><meshStandardMaterial color="#fff9e9" /></mesh>)}
      <mesh position={[0, 1.12, 0.59]}><planeGeometry args={[1.14, 0.36]} /><meshBasicMaterial map={sign} /></mesh>
      <mesh position={[0, 1.58, 0]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.22, 0.22, 0.08, 16]} /><meshStandardMaterial color="#ffd461" metalness={0.4} roughness={0.3} /></mesh>
    </group>
  );
}

function NeutralLandmark({ tileId }: { tileId: number }): React.JSX.Element {
  if (tileId === 8) return <BankBuilding />;

  return (
    <group>
      <mesh position={[0, 0.07, 0]}>
        <cylinderGeometry args={[0.62, 0.7, 0.14, 8]} />
        <meshStandardMaterial color="#b9d889" roughness={0.92} />
      </mesh>
      <Tree position={[-0.2, 0.08, 0.05]} scale={0.7} />
      <mesh position={[0.32, 0.22, 0.12]}>
        <boxGeometry args={[0.5, 0.1, 0.16]} />
        <meshStandardMaterial color="#d49a63" roughness={0.9} />
      </mesh>
    </group>
  );
}

function ClockTower(): React.JSX.Element {
  return (
    <group position={[0, 0.02, 0]}>
      <mesh position={[0, 0.14, 0]}>
        <cylinderGeometry args={[2.25, 2.4, 0.28, 12]} />
        <meshStandardMaterial color="#92c89e" roughness={0.9} />
      </mesh>
      <mesh position={[0, 1.18, 0]}>
        <boxGeometry args={[1.15, 2.05, 1.15]} />
        <meshStandardMaterial color="#f6d993" roughness={0.78} />
      </mesh>
      <mesh position={[0, 2.38, 0]} rotation={[0, Math.PI / 4, 0]}>
        <coneGeometry args={[1.02, 0.82, 4]} />
        <meshStandardMaterial color="#d15b4e" roughness={0.72} />
      </mesh>
      {[0, Math.PI / 2, Math.PI, -Math.PI / 2].map(angle => (
        <mesh key={angle} position={[Math.sin(angle) * 0.581, 1.42, Math.cos(angle) * 0.581]} rotation={[0, angle, 0]}>
          <circleGeometry args={[0.27, 16]} />
          <meshStandardMaterial color="#fff9df" roughness={0.5} />
        </mesh>
      ))}
      <mesh position={[0, 2.94, 0]}>
        <sphereGeometry args={[0.13, 8, 6]} />
        <meshStandardMaterial color="#f8c95d" metalness={0.2} roughness={0.45} />
      </mesh>
      <Tree position={[-1.55, 0.18, -1.3]} scale={0.9} />
      <Tree position={[1.4, 0.18, 1.55]} scale={0.82} />
      <Tree position={[-1.5, 0.18, 1.45]} scale={0.65} />
      <Lamp position={[1.55, 0.18, -1.35]} />
    </group>
  );
}

export function MiniatureTown({ game }: TownProps): React.JSX.Element {
  return (
    <group>
      <mesh position={[0, -0.82, 0]}>
        <cylinderGeometry args={[8.35, 8.75, 0.72, 12]} />
        <meshStandardMaterial color="#745846" roughness={1} />
      </mesh>
      <mesh position={[0, -0.42, 0]}>
        <cylinderGeometry args={[8.15, 8.25, 0.26, 12]} />
        <meshStandardMaterial color="#8ecf99" roughness={0.94} />
      </mesh>
      <mesh position={[0, -1.2, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[22, 48]} />
        <meshStandardMaterial color="#76c7cc" roughness={0.38} metalness={0.02} />
      </mesh>

      {TILE_ANCHORS.map((point, index) => (
        <group key={`road-${index}`} position={[point.x, -0.02, point.z]}>
          <mesh>
            <boxGeometry args={[1.78, 0.19, 1.78]} />
            <meshStandardMaterial color={index === 0 ? '#f4cc5c' : '#dbe2d6'} roughness={0.88} />
          </mesh>
          <mesh position={[0, 0.101, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.13, 0.17, 16]} />
            <meshBasicMaterial color={index === 0 ? '#fff9d9' : '#9eb4a6'} side={THREE.DoubleSide} />
          </mesh>
        </group>
      ))}

      {TILE_ANCHORS.map((point, index) => {
        const next = TILE_ANCHORS[(index + 1) % TILE_ANCHORS.length];
        const horizontal = point.z === next.z;
        return (
          <mesh key={`edge-${index}`} position={[(point.x + next.x) / 2, -0.03, (point.z + next.z) / 2]}>
            <boxGeometry args={horizontal ? [2, 0.17, 0.72] : [0.72, 0.17, 2]} />
            <meshStandardMaterial color="#dbe2d6" roughness={0.88} />
          </mesh>
        );
      })}

      {game.tiles.map(tile => {
        const lot = LOT_ANCHORS[tile.id];
        const road = TILE_ANCHORS[tile.id];
        const inwardAngle = Math.abs(road.z) === 4 ? (road.z < 0 ? 0 : Math.PI) : (road.x > 0 ? -Math.PI / 2 : Math.PI / 2);
        return (
          <group key={tile.id} position={[lot.x, -0.03, lot.z]} rotation={[0, inwardAngle, 0]}>
            {tile.kind === 'property' ? <House tile={tile} /> : <NeutralLandmark tileId={tile.id} />}
          </group>
        );
      })}

      {/* Shared walls and roof strips visibly join only eligible street neighbours. */}
      {rowHouses(game).flatMap(row => row.tileIds.slice(1).map((id, index) => {
        const a = LOT_ANCHORS[row.tileIds[index]];
        const b = LOT_ANCHORS[id];
        const horizontal = a.z === b.z;
        const height = Math.min(game.tiles[id].level ?? 1, game.tiles[row.tileIds[index]].level ?? 1) === 2 ? 1.45 : 0.85;
        return (
          <group key={`terrace-${id}`} position={[(a.x + b.x) / 2, 0, (a.z + b.z) / 2]}>
            <mesh position={[0, height / 2 + 0.13, 0]}>
              <boxGeometry args={horizontal ? [1.22, height, 0.72] : [0.72, height, 1.22]} />
              <meshStandardMaterial color={row.ownerId === 'p1' ? '#ffb278' : '#91b5ff'} roughness={0.78} />
            </mesh>
            <mesh position={[0, height + 0.2, 0]}>
              <boxGeometry args={horizontal ? [1.35, 0.18, 0.86] : [0.86, 0.18, 1.35]} />
              <meshStandardMaterial color={row.ownerId === 'p1' ? '#c85045' : '#385da9'} />
            </mesh>
          </group>
        );
      }))}

      <ClockTower />
      <Lamp position={[-2.9, 0.08, -2.9]} />
      <Lamp position={[2.9, 0.08, -2.9]} />
      <Lamp position={[-2.9, 0.08, 2.9]} />
      <Lamp position={[2.9, 0.08, 2.9]} />
    </group>
  );
}

