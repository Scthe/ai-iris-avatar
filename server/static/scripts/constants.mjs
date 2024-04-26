export const GITHUB_LINK = 'https://github.com/Scthe/ai-iris-avatar';

/** 'ws://localhost:8080/ws' */
export const SOCKET_URL = `ws://${location.host}/`;

export const HARD_SPACE = '\u00A0';

export const INPUT_PLACEHOLDER = 'Ask me a question!';

export const SECRET_HARDCODED_QUESTION = 'Who is Michael Jordan?';

export const SOCKET_STATE = {
  connecting: 'connecting',
  open: 'open',
  closed: 'closed',
};

export const MSG_TYPE = {
  user: 'user',
  ai: 'ai',
  system: 'system',
};

export const SYSTEM_MSG_TYPE = {
  contextReset: 'contextReset',
  socketConnected: 'socketConnected',
  socketDisconnected: 'socketDisconnected',
  intro: 'intro',
};

export const SYSTEM_MSG_PROPS = {
  contextReset: { text: 'Chat context reset' },
  socketConnected: { text: 'Socket connected' },
  socketDisconnected: { text: 'Error: Socket disconnected', isError: true },
  intro: { isIntro: true },
};

export const INSTRUCTION_MESSAGES = [];

export const AVAILABLE_VFX = [
  'None',
  'ColorGradientVFX',
  'TinyPinkRibbonsVFX',
  'SnowVFX',
  'PoppingRedCirclesVFX',
  'RainVFX',
  'BluePurpleFloatingVFX',
];
