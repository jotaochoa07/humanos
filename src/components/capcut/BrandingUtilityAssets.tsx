import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {HumanosBrandReveal} from '../HumanosBrandReveal';
import {HUMANOS_COLORS} from '../../styles/tokens';
import {humanosPreviewConfig} from '../../config/humanosConfig';

export const LongBrandCategories: React.FC = () => {
  return <HumanosBrandReveal {...humanosPreviewConfig.brandReveal} title="" />;
};

export const LongCyanLinePulse: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12, 62, 84], [0, 0.72, 0.72, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const scaleX = interpolate(frame, [0, 18, 72, 90], [0.05, 1, 1, 0.05], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.inOut(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{backgroundColor: HUMANOS_COLORS.black}}>
      <div
        style={{
          position: 'absolute',
          left: 310,
          top: 960,
          width: 460,
          height: 2,
          backgroundColor: HUMANOS_COLORS.cyan,
          opacity,
          transform: `scaleX(${scaleX})`,
          transformOrigin: 'center',
        }}
      />
    </AbsoluteFill>
  );
};

export const HumanosBackgroundLoop: React.FC = () => {
  const frame = useCurrentFrame();
  const breath = Math.sin(frame / 36) * 0.012;
  return (
    <AbsoluteFill style={{backgroundColor: HUMANOS_COLORS.black, overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          transform: `scale(${1 + breath})`,
          background:
            'radial-gradient(circle at 50% 48%, rgba(255,255,255,0.055), rgba(2,3,4,0) 44%)',
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.045,
          backgroundImage:
            'radial-gradient(circle, rgba(255,255,255,0.5) 0 1px, transparent 1px)',
          backgroundSize: `${11 + (frame % 2)}px ${13 + (frame % 3)}px`,
          mixBlendMode: 'screen',
        }}
      />
    </AbsoluteFill>
  );
};
