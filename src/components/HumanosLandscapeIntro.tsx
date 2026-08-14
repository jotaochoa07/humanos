import React from 'react';
import {AbsoluteFill, Audio, Easing, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS, HUMANOS_TYPE} from '../styles/tokens';

/**
 * Landscape-only HUMANOS intro. This deliberately keeps the existing portrait
 * reveal components untouched: its word layout is authored for 1920×1080.
 */
const WORDS = [
  {label: 'FOUNDERS', x: 110, y: 106, size: 38, tone: 'muted'},
  {label: 'BUILDERS', x: 1262, y: 124, size: 44, tone: 'muted'},
  {label: 'DREAMERS', x: 126, y: 700, size: 46, tone: 'white'},
  {label: 'CREATORS', x: 1372, y: 742, size: 50, tone: 'white'},
  {label: 'ARTISTS', x: 1336, y: 930, size: 34, tone: 'muted'},
] as const;

export const HumanosLandscapeIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const easing = Easing.bezier(0.16, 1, 0.3, 1);

  return (
    <AbsoluteFill style={{backgroundColor: '#090909', color: HUMANOS_COLORS.white, overflow: 'hidden'}}>
      <Audio src={staticFile('humanos/intro-heartbeat.mp3')} volume={0.12} />
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse at 50% 49%, rgba(255,255,255,0.048) 0%, rgba(9,9,9,0) 45%), radial-gradient(ellipse at 71% 26%, rgba(1,201,199,0.035) 0%, rgba(9,9,9,0) 30%)',
        }}
      />

      {WORDS.map((word, index) => (
        <div
          key={word.label}
          style={{
            position: 'absolute',
            left: word.x,
            top: word.y,
            fontFamily: HUMANOS_TYPE.landscapeBrand,
            fontSize: word.size,
            fontWeight: word.tone === 'white' ? 700 : 500,
            letterSpacing: word.size > 45 ? 7 : 5,
            color: word.tone === 'white' ? HUMANOS_COLORS.white : 'rgba(255, 255, 255, 0.47)',
            opacity: interpolate(frame, [index * 5, index * 5 + 22, 112, 129], [0, 1, 1, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing,
            }),
            translate: `${interpolate(frame, [0, 129], [index % 2 === 0 ? -12 : 12, index % 2 === 0 ? 9 : -9], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })}px ${interpolate(frame, [0, 129], [index % 2 === 0 ? 9 : -9, index % 2 === 0 ? -7 : 7], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })}px`,
            whiteSpace: 'nowrap',
          }}
        >
          {word.label}
        </div>
      ))}

      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: HUMANOS_TYPE.landscapeBrand,
          fontSize: 142,
          fontWeight: 800,
          letterSpacing: 20,
          color: HUMANOS_COLORS.cyan,
          opacity: interpolate(frame, [32, 52, 74, 94, 114, 129], [0, 0.08, 0.28, 0.62, 1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.inOut(Easing.cubic),
          }),
          filter: `blur(${interpolate(frame, [32, 58, 88, 108, 120], [24, 16, 7, 2, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.inOut(Easing.cubic),
          })}px)`,
          translate: `0px ${interpolate(frame, [32, 112], [70, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.inOut(Easing.cubic),
          })}px`,
          scale: interpolate(frame, [32, 112], [0.88, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            easing: Easing.inOut(Easing.cubic),
          }),
        }}
      >
        HUMANOS
      </div>
    </AbsoluteFill>
  );
};
