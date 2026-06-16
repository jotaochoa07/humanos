import {staticFile} from 'remotion';

export const humanosPreviewConfig = {
  brandReveal: {
    title: 'HUMANOS',
    categories: [
      'FOUNDERS',
      'BUILDERS',
      'INVENTORS',
      'DREAMERS',
      'CREATORS',
      'SCIENTISTS',
      'ARTISTS',
      'MAKERS',
    ],
  },
  characterCard: {
    archetype: 'BUILDER',
    name: 'JAN KOUM',
    descriptor: 'Fundador de WhatsApp',
    imageSrc: staticFile('humanos/jan-koum-portrait.jpg'),
    layoutVariant: 'portraitDominant' as const,
  },
  characterCardVariantA: {
    archetype: 'BUILDER',
    name: 'JAN KOUM',
    descriptor: 'Fundador de WhatsApp',
    imageSrc: staticFile('humanos/jan-koum-portrait.jpg'),
    layoutVariant: 'signature' as const,
  },
  endCard: {
    phrase: 'HISTORIAS de HUMANOS\nhaciendo HISTORIA',
    brand: 'HUMANOS',
  },
};
