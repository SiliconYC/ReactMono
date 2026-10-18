import { useLayoutEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { GameState } from '../../core/game.js';
import type { OutcomeCue } from '../outcomes.js';
import { positionForTile } from './layout.js';

const CONFETTI_COLORS = ['#ffd765', '#ff8e73', '#70c9bc', '#91a9ff'];

/** Original geometry, anchored to the winning player's settled tile. No game writes or timers. */
export function OutcomeCelebration({ game, cue, reducedMotion }: {
  game: GameState;
  cue: OutcomeCue;
  reducedMotion: boolean;
}): React.JSX.Element | null {
  const trophy = useRef<THREE.Group>(null);
  const halo = useRef<THREE.Mesh>(null);
  const confetti = useRef<THREE.Group>(null);
  const elapsed = useRef(0);
  const winner = game.players.find(player => player.id === cue.winnerId);
  const point = positionForTile(winner?.position ?? 0);
  const draw = cue.stage === 'draw';
  const winnerSeat = game.players.findIndex(player => player.id === cue.winnerId);
  const seatOffset = winnerSeat === 0 ? -0.22 : 0.22;

  useLayoutEffect(() => {
    elapsed.current = 0;
    if (trophy.current) {
      trophy.current.position.set(0, 2.1, 0);
      trophy.current.rotation.set(0, 0, 0);
      trophy.current.scale.setScalar(1);
    }
    if (halo.current) halo.current.scale.setScalar(1);
  }, [cue.nonce, cue.stage, cue.winnerId, reducedMotion]);

  useFrame((_, delta) => {
    elapsed.current = Math.min(elapsed.current + delta, 2);
    const progress = Math.min(elapsed.current / 1.9, 1);
    if (trophy.current && !reducedMotion) {
      trophy.current.position.y = 2.1 + Math.sin(progress * Math.PI) * 0.25;
      trophy.current.rotation.y = Math.sin(progress * Math.PI) * 0.45;
    }
    if (halo.current) {
      halo.current.scale.setScalar(reducedMotion ? 1 : 1 + Math.sin(progress * Math.PI) * (draw ? 0.1 : 0.22));
    }
    confetti.current?.children.forEach((piece, index) => {
      const angle = index * 2.39996;
      if (reducedMotion) {
        piece.visible = false;
        return;
      }
      const local = THREE.MathUtils.clamp((elapsed.current - (index % 4) * 0.075) / 1.5, 0, 1);
      const radius = 0.55 + local * 1.2;
      piece.position.set(Math.cos(angle) * radius, 2.5 + Math.sin(local * Math.PI) * 1.1 - local * 2.1, Math.sin(angle) * radius);
      piece.rotation.set(local * Math.PI * 2, angle + local * Math.PI, local * Math.PI);
      piece.scale.setScalar(1 - Math.pow(local, 5));
      piece.visible = local > 0 && local < 1;
    });
  });

  if (cue.stage === 'bankrupt') return null;
  if (!draw && !winner) return null;

  return (
    <group position={draw ? [0, 0.31, 0] : [point.x + seatOffset, 0.31, point.z - seatOffset]}>
      <mesh ref={halo} position={[0, -0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={draw ? [1.5, 1.65, 48] : [0.7, 0.85, 40]} />
        <meshBasicMaterial color={draw ? '#b8ece1' : '#ffe18a'} transparent opacity={0.85} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      {draw ? (
        <group position={[0, 1.1, 0]}>
          {[-0.4, 0.4].map(x => (
            <mesh key={x} position={[x, 0, 0]} rotation={[Math.PI / 2, 0, 0]}>
              <torusGeometry args={[0.55, 0.07, 6, 24]} />
              <meshStandardMaterial color="#dbf6ed" emissive="#7bbeb2" emissiveIntensity={0.2} roughness={0.5} />
            </mesh>
          ))}
        </group>
      ) : (
        <>
          <group ref={trophy} position={[0, 2.1, 0]}>
            <mesh position={[0, 0.3, 0]}>
              <cylinderGeometry args={[0.38, 0.14, 0.5, 8]} />
              <meshStandardMaterial color="#ffdb67" metalness={0.55} roughness={0.3} />
            </mesh>
            <mesh position={[0, -0.08, 0]}>
              <cylinderGeometry args={[0.075, 0.075, 0.35, 8]} />
              <meshStandardMaterial color="#eab642" metalness={0.5} roughness={0.35} />
            </mesh>
            <mesh position={[0, -0.29, 0]}>
              <cylinderGeometry args={[0.3, 0.32, 0.1, 8]} />
              <meshStandardMaterial color="#d9a33b" metalness={0.45} roughness={0.35} />
            </mesh>
            {[-1, 1].map(side => (
              <mesh key={side} position={[side * 0.34, 0.3, 0]}>
                <torusGeometry args={[0.18, 0.045, 5, 12]} />
                <meshStandardMaterial color="#ffdb67" metalness={0.5} roughness={0.3} />
              </mesh>
            ))}
          </group>
          {!reducedMotion && (
            <group ref={confetti}>
              {Array.from({ length: 20 }, (_, index) => (
                <mesh key={index} visible={false}>
                  <boxGeometry args={[0.09, 0.04, 0.17]} />
                  <meshStandardMaterial color={CONFETTI_COLORS[index % CONFETTI_COLORS.length]} roughness={0.7} />
                </mesh>
              ))}
            </group>
          )}
        </>
      )}
    </group>
  );
}
