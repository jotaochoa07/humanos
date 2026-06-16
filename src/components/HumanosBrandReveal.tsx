import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS, HUMANOS_TYPE} from '../styles/tokens';

export type HumanosBrandRevealProps = {
  title: string;
  categories: string[];
  accentColor?: string;
};

const memoryLayers = [
  {x: 122, y: 516, scale: 0.92, blur: 2.8, opacity: 0.18, drift: -8},
  {x: 668, y: 650, scale: 1.28, blur: 0.9, opacity: 0.42, drift: 6},
  {x: 258, y: 790, scale: 0.74, blur: 4.2, opacity: 0.14, drift: 10},
  {x: 790, y: 900, scale: 1.24, blur: 0.9, opacity: 0.42, drift: -7},
  {x: 235, y: 1058, scale: 1.08, blur: 1.5, opacity: 0.34, drift: 5},
  {x: 560, y: 1168, scale: 0.82, blur: 3.4, opacity: 0.17, drift: -4},
  {x: 930, y: 1292, scale: 1.18, blur: 2.6, opacity: 0.2, drift: 8},
  {x: 320, y: 1405, scale: 0.68, blur: 4.8, opacity: 0.12, drift: -6},
];

export const HumanosBrandReveal: React.FC<HumanosBrandRevealProps> = ({
  title,
  categories,
  accentColor = HUMANOS_COLORS.cyan,
}) => {
  const frame = useCurrentFrame();
  const breath = Math.sin(frame / 18) * 0.012;
  const categoryFade = interpolate(frame, [0, 8, 22, 28], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const titleOpacity = interpolate(frame, [40, 50], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const titleScale = interpolate(frame, [40, 54], [0.93, 1.03], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const pulseOpacity = interpolate(frame, [26, 29, 33], [0, 0.62, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: HUMANOS_COLORS.black, overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          transform: `scale(${1 + breath})`,
          background:
            'radial-gradient(circle at 48% 49%, rgba(255,255,255,0.06), rgba(2,3,4,0) 44%)',
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.05,
          backgroundImage:
            'radial-gradient(circle at 18% 22%, rgba(255,255,255,0.55) 0 1px, transparent 1px), radial-gradient(circle at 72% 64%, rgba(255,255,255,0.42) 0 1px, transparent 1px)',
          backgroundSize: '9px 11px, 13px 15px',
          mixBlendMode: 'screen',
        }}
      />

      {categories.slice(0, memoryLayers.length).map((category, index) => {
        const layer = memoryLayers[index];
        const convergence = interpolate(frame, [7, 29], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing: Easing.inOut(Easing.cubic),
        });
        const x = layer.x + (540 - layer.x) * convergence * 0.2;
        const y = layer.y + (960 - layer.y) * convergence * 0.16 + Math.sin(frame / 18 + index) * layer.drift;
        const scale = layer.scale + (1 - layer.scale) * convergence * 0.2;
        const blur = layer.blur + 2.0 * convergence;

        return (
          <div
            key={category}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              transform: `translate(-50%, -50%) scale(${scale})`,
              color: HUMANOS_COLORS.white,
              fontFamily: HUMANOS_TYPE.brand,
              fontSize: 42,
              letterSpacing: 8,
              fontWeight: 600,
              opacity: categoryFade * layer.opacity,
              filter: `blur(${blur}px)`,
              whiteSpace: 'nowrap',
            }}
          >
            {category}
          </div>
        );
      })}

      <div
        style={{
          position: 'absolute',
          left: 330,
          top: 960,
          width: 420,
          height: 2,
          backgroundColor: accentColor,
          opacity: pulseOpacity,
          transform: `scaleX(${interpolate(frame, [26, 29], [0.08, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })})`,
          transformOrigin: 'center',
        }}
      />

      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: HUMANOS_COLORS.white,
          fontFamily: HUMANOS_TYPE.brand,
          fontSize: 104,
          letterSpacing: 16,
          fontWeight: 700,
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
        }}
      >
        {title}
      </div>
    </AbsoluteFill>
  );
};
