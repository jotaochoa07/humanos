import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS, HUMANOS_TYPE} from '../../styles/tokens';

type SlowCategoryThoughtsProps = {
  categories: string[];
};

const placements = [
  {x: 145, y: 510, scale: 0.82, blur: 2.4, opacity: 0.26, driftX: -10, driftY: 6},
  {x: 676, y: 680, scale: 1.22, blur: 0.8, opacity: 0.5, driftX: 8, driftY: -6},
  {x: 254, y: 850, scale: 0.72, blur: 3.8, opacity: 0.2, driftX: 12, driftY: 8},
  {x: 778, y: 1010, scale: 1.02, blur: 1.8, opacity: 0.32, driftX: -8, driftY: 6},
  {x: 330, y: 1220, scale: 0.94, blur: 2.8, opacity: 0.24, driftX: 8, driftY: -8},
  {x: 830, y: 1370, scale: 0.68, blur: 4.6, opacity: 0.16, driftX: -6, driftY: 8},
];

export const SlowCategoryThoughts: React.FC<SlowCategoryThoughtsProps> = ({categories}) => {
  const frame = useCurrentFrame();
  const breath = Math.sin(frame / 42) * 0.01;

  return (
    <AbsoluteFill style={{backgroundColor: HUMANOS_COLORS.black, overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          transform: `scale(${1 + breath})`,
          background:
            'radial-gradient(circle at 50% 48%, rgba(255,255,255,0.052), rgba(2,3,4,0) 44%)',
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.04,
          backgroundImage:
            'radial-gradient(circle, rgba(255,255,255,0.48) 0 1px, transparent 1px)',
          backgroundSize: `${11 + (frame % 2)}px ${13 + (frame % 3)}px`,
          mixBlendMode: 'screen',
        }}
      />

      {categories.slice(0, placements.length).map((category, index) => {
        const basePlacement = placements[index];
        const isLongWord = category.length > 11;
        const p = isLongWord
          ? {...basePlacement, x: Math.max(520, basePlacement.x), scale: Math.min(basePlacement.scale, 0.78), blur: Math.min(basePlacement.blur, 2.2), opacity: Math.max(basePlacement.opacity, 0.28)}
          : basePlacement;
        const start = 6 + index * 12;
        const opacity = interpolate(frame, [start, start + 24, 104, 120], [0, p.opacity, p.opacity, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.out(Easing.cubic),
        });
        const entry = interpolate(frame, [start, start + 34], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.out(Easing.cubic),
        });
        const floatX = Math.sin(frame / 38 + index) * p.driftX;
        const floatY = Math.cos(frame / 44 + index) * p.driftY;

        return (
          <div
            key={`${category}-${index}`}
            style={{
              position: 'absolute',
              left: p.x + floatX,
              top: p.y + floatY + (1 - entry) * 22,
              transform: `translate(-50%, -50%) scale(${p.scale})`,
              color: HUMANOS_COLORS.white,
              fontFamily: HUMANOS_TYPE.brand,
              fontSize: isLongWord ? 36 : 42,
              letterSpacing: isLongWord ? 5 : 8,
              fontWeight: 600,
              opacity,
              filter: `blur(${p.blur}px)`,
              whiteSpace: 'nowrap',
            }}
          >
            {category}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
