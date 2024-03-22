import { h, render } from 'https://esm.sh/preact';
import { useCallback, useRef, useEffect } from 'https://esm.sh/preact/hooks';
import htm from 'https://esm.sh/htm';

import {
  GITHUB_LINK,
  HARD_SPACE,
  SOCKET_STATE,
  MSG_TYPE,
  SYSTEM_MSG_PROPS,
  INPUT_PLACEHOLDER,
  SECRET_HARDCODED_QUESTION,
} from './scripts/constants.mjs';
import { useMessagesState } from './scripts/messagesState.mjs';
import { cx, useIsWindowScrolledToBottomRef } from './scripts/utils.mjs';

// Initialize htm with Preact
const html = htm.bind(h);

function MessageMeta({ type, meta }) {
  meta = type === MSG_TYPE.ai ? meta : undefined;
  if (meta == undefined) {
    return undefined;
  }

  const { elapsed_llm, elapsed_tts } = meta;
  const fmtElapsed = (time) =>
    typeof time === 'number' ? `${time.toFixed(2)}s` : '(processing)';

  return html`<div class="message-meta">
    <p>Elapsed LLM: <span class="colored">${fmtElapsed(elapsed_llm)}</span></p>
    <p>Elapsed TTS: <span class="colored">${fmtElapsed(elapsed_tts)}</span></p>
  </div>`;
}

function Message({ type, text, meta, error, status }) {
  // console.log({ ...arguments[0] });
  meta = type === MSG_TYPE.ai ? meta : undefined;

  const systemMsgProps = SYSTEM_MSG_PROPS[status];
  // console.log(systemMsgProps);
  text =
    type === MSG_TYPE.system && systemMsgProps && systemMsgProps.text
      ? systemMsgProps.text
      : text;
  text = type === MSG_TYPE.ai && error ? `Error: ${error}` : text;

  const cl = cx('message', {
    'message-user': type === MSG_TYPE.user,
    'message-system': type === MSG_TYPE.system,
    'message-system-error': type === MSG_TYPE.system && systemMsgProps?.isError,
    'message-system-intro': type === MSG_TYPE.system && systemMsgProps?.isIntro,
    'message-ai': type === MSG_TYPE.ai,
    'message-ai-empty': type === MSG_TYPE.ai && text.length == 0,
    'message-ai-error': type === MSG_TYPE.ai && error,
  });

  return html`<li class="${cl}">
    <p class="message-text">${text || HARD_SPACE}</p>
    <${MessageMeta} type=${type} meta=${meta} />
  </li>`;
}

function MessageContainer({ messages }) {
  return html`<div class="message-container-wrapper">
    <ul>
      ${messages.map((m) => html`<${Message} key="${m.id}" ...${m} />`)}
    </ul>
  </div>`;
}

function UserInput({ actionSendMessage, actionReconnect, socketState }) {
  const iconSize = '30px';

  const sendMessagesRef = useRef([SECRET_HARDCODED_QUESTION]);
  const prevMessagesIndexRef = useRef(-1);

  const onInputKeyDown = useCallback((e) => {
    const inputEl = document.getElementById('user-input-field');
    const msgIdxMods = { ArrowUp: 1, ArrowDown: -1 };
    const msgIdxMod = msgIdxMods[e.code];
    if (msgIdxMod == null || !inputEl) {
      prevMessagesIndexRef.current = -1;
      return;
    }

    // user pressed arrow up/down: restore historical message
    e.preventDefault();
    const historyMsgIdx = prevMessagesIndexRef.current + msgIdxMod;
    const historicalMsg = sendMessagesRef.current[historyMsgIdx];
    if (historicalMsg != null) {
      inputEl.value = historicalMsg;
      prevMessagesIndexRef.current = historyMsgIdx;
    }
  }, []);

  const onMessageSend = useCallback(
    (e) => {
      e.preventDefault();
      const inputEl = document.getElementById('user-input-field');
      let text = inputEl.value.trim();
      if (text.length === 0) return;

      sendMessagesRef.current.unshift(text);
      inputEl.value = '';
      actionSendMessage(text);
    },
    [actionSendMessage]
  );

  const onReconnect = useCallback(
    (e) => {
      e.preventDefault();
      actionReconnect();
    },
    [actionReconnect]
  );

  if (socketState === SOCKET_STATE.closed) {
    return html`<div class="user-input">
      <button
        type="button"
        title="Try reconnect"
        class="user-input-reconnect-btn reset-focus-states"
        onClick=${onReconnect}
      >
        <p>Try reconnect</p>
        <${ReconnectIcon} iconSize=${iconSize} />
      </button>
    </div>`;
  }

  if (socketState === SOCKET_STATE.connecting) {
    return html`<div class="user-input user-input-reconnecting">
      <p>Connecting...</p>
    </div>`;
  }

  return html`<div class="user-input">
    <form onSubmit=${onMessageSend}>
      <div class="user-input-content">
        <div>
          <a
            href=${GITHUB_LINK}
            title="See the repo on GitHub"
            target="_blank"
            rel="noopener noreferrer"
            class="github-btn reset-focus-states"
          >
            <${GitHubIcon} iconSize=${iconSize} />
          </a>
        </div>
        <input
          id="user-input-field"
          name="user-input-field"
          class="user-input-field"
          placeholder=${INPUT_PLACEHOLDER}
          autocomplete="off"
          onkeydown=${onInputKeyDown}
        />
        <div>
          <button
            type="submit"
            title="Send the question"
            class="user-input-side-btn reset-focus-states"
          >
            <${SendIcon} iconSize=${iconSize} />
          </button>
        </div>
      </div>
    </form>
  </div>`;
}

function App() {
  const { state, socketState, actionReconnect, actionSendMessage } =
    useMessagesState();
  const { messages } = state;

  const isWindowScrolledBtmRef = useIsWindowScrolledToBottomRef();

  useEffect(() => {
    if (isWindowScrolledBtmRef.current) {
      window.scrollTo({
        top: document.body.offsetHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  return html`<main class="app-container">
    <audio id="audio" controls autoplay hidden></audio>
    <${MessageContainer} messages=${messages} />
    <${UserInput}
      actionSendMessage=${actionSendMessage}
      actionReconnect=${actionReconnect}
      socketState=${socketState}
    />
  </main>`;
}

render(html`<${App} />`, app);

///////////////////////////////////
///////////////////////////////////
///////////////////////////////////
/// Icons below, just ignore..
export function SendIcon({ iconSize }) {
  return html`<svg
    xmlns="http://www.w3.org/2000/svg"
    width="${iconSize}"
    height="${iconSize}"
    fill="currentcolor"
    viewBox="0 0 256 256"
    aria-hidden="true"
  >
    <path
      d="M231.4,44.34s0,.1,0,.15l-58.2,191.94a15.88,15.88,0,0,1-14,11.51q-.69.06-1.38.06a15.86,15.86,0,0,1-14.42-9.15l-35.71-75.39a4,4,0,0,1,.79-4.54l57.26-57.27a8,8,0,0,0-11.31-11.31L97.08,147.6a4,4,0,0,1-4.54.79l-75-35.53A16.37,16.37,0,0,1,8,97.36,15.89,15.89,0,0,1,19.57,82.84l191.94-58.2.15,0A16,16,0,0,1,231.4,44.34Z"
    ></path>
  </svg>`;
}

export function ReconnectIcon({ iconSize }) {
  return html`<svg
    xmlns="http://www.w3.org/2000/svg"
    width="${iconSize}"
    height="${iconSize}"
    fill="currentcolor"
    viewBox="0 0 256 256"
    aria-hidden="true"
  >
    <path
      d="M197.66,186.34a8,8,0,0,1,0,11.32C196.58,198.73,170.82,224,128,224c-23.36,0-46.13-9.1-66.28-26.41L45.66,213.66A8,8,0,0,1,32,208V160a8,8,0,0,1,8-8H88a8,8,0,0,1,5.66,13.66L73.08,186.24C86.08,197.15,104.83,208,128,208c36.27,0,58.13-21.44,58.34-21.66A8,8,0,0,1,197.66,186.34Zm21.4-145.73a8,8,0,0,0-8.72,1.73L194.28,58.41C174.13,41.1,151.36,32,128,32,85.18,32,59.42,57.27,58.34,58.34A8,8,0,0,0,69.66,69.66C69.87,69.44,91.73,48,128,48c23.17,0,41.92,10.85,54.92,21.76L162.34,90.34A8,8,0,0,0,168,104h48a8,8,0,0,0,8-8V48A8,8,0,0,0,219.06,40.61Z"
    ></path>
  </svg>`;
}

export function GitHubIcon({ iconSize }) {
  return html`<svg
    xmlns="http://www.w3.org/2000/svg"
    width="${iconSize}"
    height="${iconSize}"
    fill="currentcolor"
    viewBox="0 0 24 24"
    aria-hidden="true"
  >
    <path
      d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
    />
  </svg>`;
}
