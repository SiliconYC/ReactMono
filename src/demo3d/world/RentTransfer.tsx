import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { GameState } from '../../core/game.js';
import type { RentCue } from '../presentation.js';
import { positionForTile } from './layout.js';

/** World-space coins connect the landed tile to the receiving player's position. */
export function RentTransfer({ game, cue, reducedMotion }: { game: GameState; cue: RentCue; reducedMotion: boolean }): React.JSX.Element | null {
  const root = useRef<THREE.Group>(null);
  const elapsed = useRef(0);
  const from = positionForTile(cue.tileId);
  const recipient = game.players.find(player => player.id === cue.toId);
  const to = positionForTile(recipient?.position ?? cue.tileId);
  useFrame((_, delta) => {
    elapsed.current += delta;
    root.current?.children.forEach((coin, index) => {
      const progress = THREE.MathUtils.clamp((elapsed.current - index * 0.1) / 1.1, 0, 1);
      coin.position.set(
        THREE.MathUtils.lerp(from.x, to.x, progress),
        1.5 + Math.sin(progress * Math.PI) * 2,
        THREE.MathUtils.lerp(from.z, to.z, progress)
      );
      coin.rotation.set(Math.PI / 2, progress * Math.PI * 5, 0);
      coin.visible = progress > 0 && progress < 1;
    });
  });
  if (reducedMotion) return null;
  return (
    <group ref={root}>
      {Array.from({ length: 6 }, (_, index) => (
        <mesh key={index} visible={false}>
          <cylinderGeometry args={[0.17, 0.17, 0.07, 12]} />
          <meshStandardMaterial color="#ffcf45" emissive="#edaa25" emissiveIntensity={0.45} metalness={0.45} roughness={0.3} />
        </mesh>
      ))}
    </group>
  );
}
