import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS, HUMANOS_TYPE} from '../styles/tokens';

export type HumanosEndCardProps = {
  phrase: string;
  brand: string;
  accentColor?: string;
};

export const HumanosEndCard: React.FC<HumanosEndCardProps> = ({
  brand,
  accentColor = HUMANOS_COLORS.cyan,
}) => {
  const frame = useCurrentFrame();
  const topOpacity = interpolate(frame, [0, 12, 28, 38], [0, 1, 1, 0.24], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const brandOpacity = interpolate(frame, [20, 34, 55, 66], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const historyOpacity = interpolate(frame, [50, 63], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const pulseOpacity = interpolate(frame, [43, 46, 50], [0, 0.82, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const brandScale = interpolate(frame, [20, 36], [0.955, 1.02], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const breath = Math.sin(frame / 24) * 0.01;

  return (
    <AbsoluteFill style={{backgroundColor: HUMANOS_COLORS.black}}>
      <AbsoluteFill
        style={{
          transform: `scale(${1 + breath})`,
          background:
            'radial-gradient(circle at 50% 48%, rgba(255,255,255,0.055), rgba(2,3,4,0) 44%)',
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.04,
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.5) 0 1px, transparent 1px)',
          backgroundSize: '11px 13px',
          mixBlendMode: 'screen',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 96,
          right: 96,
          top: 660,
          color: HUMANOS_COLORS.mutedWhite,
          fontFamily: HUMANOS_TYPE.brand,
          fontSize: 36,
          lineHeight: 1,
          fontWeight: 600,
          letterSpacing: 10,
          textAlign: 'center',
          opacity: topOpacity,
        }}
      >
        HISTORIAS DE
      </div>

      <div
        style={{
          position: 'absolute',
          left: 96,
          right: 96,
          top: 792,
          color: accentColor,
          fontFamily: HUMANOS_TYPE.brand,
          fontSize: 88,
          fontWeight: 700,
          letterSpacing: 13,
          lineHeight: 1,
          textAlign: 'center',
          opacity: brandOpacity,
          transform: `scale(${brandScale})`,
        }}
      >
        {brand}
      </div>

      <div
        style={{
          position: 'absolute',
          left: 388,
          top: 958,
          width: 304,
          height: 2,
          backgroundColor: accentColor,
          opacity: pulseOpacity,
          transform: `scaleX(${interpolate(frame, [43, 46], [0.08, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })})`,
          transformOrigin: 'center',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: 96,
          right: 96,
          top: 1068,
          color: HUMANOS_COLORS.white,
          fontFamily: HUMANOS_TYPE.body,
          fontSize: 42,
          fontWeight: 500,
          lineHeight: 1.25,
          letterSpacing: 0.8,
          textAlign: 'center',
          opacity: historyOpacity,
        }}
      >
        haciendo HISTORIA
      </div>
    </AbsoluteFill>
  );
};
