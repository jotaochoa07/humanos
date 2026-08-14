import React from 'react';
import {AbsoluteFill, Audio, Easing, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS, HUMANOS_TYPE} from '../styles/tokens';

/**
 * Native 9:16 HUMANOS intro. The composition is authored for 1080×1920 so
 * the category words use the full portrait canvas instead of cropping the
 * approved landscape treatment.
 */
export const DEFAULT_PORTRAIT_WORDS = [
  {label: 'FOUNDERS', x: 72, y: 174, size: 40, tone: 'muted', drift: -1},
  {label: 'BUILDERS', x: 536, y: 414, size: 46, tone: 'muted', drift: 1},
  {label: 'DREAMERS', x: 74, y: 1056, size: 52, tone: 'white', drift: -1},
  {label: 'CREATORS', x: 406, y: 1390, size: 56, tone: 'white', drift: 1},
  {label: 'ARTISTS', x: 108, y: 1686, size: 38, tone: 'muted', drift: -1},
] as const;

export const CAMILO_PORTRAIT_WORDS = [
  {label: 'SOÑADORES', x: 72, y: 174, size: 40, tone: 'muted', drift: -1},
  {label: 'ALTRUISTAS', x: 536, y: 414, size: 42, tone: 'muted', drift: 1},
  {label: 'GENEROSOS', x: 74, y: 1056, size: 50, tone: 'white', drift: -1},
  {label: 'UNIDOS', x: 552, y: 1390, size: 56, tone: 'white', drift: 1},
  {label: 'INSPIRADORES', x: 108, y: 1686, size: 34, tone: 'muted', drift: -1},
] as const;

type PortraitWord = (typeof DEFAULT_PORTRAIT_WORDS)[number];

export const HumanosPortraitIntro: React.FC<{words?: readonly PortraitWord[]}> = ({
  words = DEFAULT_PORTRAIT_WORDS,
}) => {
  const frame = useCurrentFrame();
  const easing = Easing.bezier(0.16, 1, 0.3, 1);

  return (
    <AbsoluteFill style={{backgroundColor: '#090909', color: HUMANOS_COLORS.white, overflow: 'hidden'}}>
      <Audio src={staticFile('humanos/intro-heartbeat.mp3')} volume={0.12} />
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse at 50% 46%, rgba(255,255,255,0.048) 0%, rgba(9,9,9,0) 42%), radial-gradient(ellipse at 64% 20%, rgba(1,201,199,0.035) 0%, rgba(9,9,9,0) 28%)',
        }}
      />

      {words.map((word, index) => (
        <div
          key={word.label}
          style={{
            position: 'absolute',
            left: word.x,
            top: word.y,
            fontFamily: HUMANOS_TYPE.landscapeBrand,
            fontSize: word.size,
            fontWeight: word.tone === 'white' ? 700 : 500,
            letterSpacing: word.size > 45 ? 8 : 6,
            color: word.tone === 'white' ? HUMANOS_COLORS.white : 'rgba(255, 255, 255, 0.47)',
            opacity: interpolate(frame, [index * 5, index * 5 + 22, 112, 129], [0, 1, 1, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
              easing,
            }),
            translate: `${interpolate(frame, [0, 129], [word.drift * 12, word.drift * -9], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            })}px ${interpolate(frame, [0, 129], [word.drift * -9, word.drift * 7], {
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
          paddingBottom: 18,
          fontFamily: HUMANOS_TYPE.landscapeBrand,
          fontSize: 126,
          fontWeight: 800,
          letterSpacing: 15,
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
          translate: `0px ${interpolate(frame, [32, 112], [86, 0], {
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
