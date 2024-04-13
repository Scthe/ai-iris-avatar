import {
  useCallback,
  useReducer,
  useEffect,
} from 'https://esm.sh/preact/hooks';

import { randId } from './utils.mjs';
import { useOnSocketMessage } from './useSocket.mjs';
import {
  SOCKET_STATE,
  MSG_TYPE,
  SYSTEM_MSG_TYPE,
  INSTRUCTION_MESSAGES,
} from './constants.mjs';

const createMessage = (type, id, rest) => ({
  id: id || randId(),
  type,
  ...rest,
});

function messagesReducer(state, action) {
  console.log('ACTION', action);

  switch (action.action) {
    case 'send': {
      const { text, respMsgId } = action;
      const alreadyContains =
        state.messages.findIndex((msg) => msg.id === respMsgId) !== -1;
      if (alreadyContains) return state;

      return {
        ...state,
        messages: [
          createMessage(MSG_TYPE.user, undefined, { text }),
          createMessage(MSG_TYPE.ai, respMsgId, { text: '' }),
          ...state.messages,
        ],
      };
    }
    case 'ai-token': {
      const { token, msgId } = action;
      return {
        ...state,
        messages: updateMessage(msgId, (m) => {
          m.text += token;
        }),
      };
    }
    case 'ai-tts-elapsed': {
      const { elapsed_tts, msgId } = action;
      return {
        ...state,
        messages: updateMessage(msgId, (m) => {
          const acc = m?.meta?.elapsed_tts || 0.0;
          m.meta = { ...(m.meta || {}), elapsed_tts: acc + elapsed_tts };
        }),
      };
    }
    case 'ai-done': {
      const { msgId, text, ...rest } = action;
      return {
        ...state,
        messages: updateMessage(msgId, (m) => {
          m.text = text;
          m.meta = { ...(m.meta || {}), ...rest };
        }),
      };
    }
    case 'ai-error': {
      const { msgId, error } = action;
      return {
        ...state,
        messages: updateMessage(msgId, (m) => {
          m.error = error;
        }),
      };
    }
    case 'system-msg': {
      const msg = createMessage(MSG_TYPE.system, undefined, {
        status: action.status,
      });
      return {
        ...state,
        messages: [msg, ...state.messages],
      };
    }
  }

  function updateMessage(id, fn) {
    return state.messages.map((m) => {
      if (m.id === id) {
        fn(m);
      }
      return m;
    });
  }

  throw Error(`Unknown action '${action.action}'.`);
}

let IS_FIRST_TIME_CONNECTING = true; // A bit hack, but..

function instructionMsg(text) {
  return {
    id: randId(),
    type: MSG_TYPE.system,
    text,
    status: SYSTEM_MSG_TYPE.intro,
  };
}

export function useMessagesState(socket) {
  const [state, dispatch] = useReducer(messagesReducer, {
    messages: INSTRUCTION_MESSAGES.map(instructionMsg),
  });

  // socket to server + message handler
  useOnSocketMessage(socket, (msg) => {
    const { msgId, type } = msg;

    switch (type) {
      case 'query': {
        // when e.g. unity client has asked a question
        const { msgId, text } = msg;
        dispatch({ action: 'send', text, respMsgId: msgId });
        break;
      }
      case 'token': {
        const { token } = msg;
        dispatch({ action: 'ai-token', msgId, token });
        break;
      }
      case 'tts-elapsed': {
        const { elapsed_tts } = msg;
        dispatch({ action: 'ai-tts-elapsed', msgId, elapsed_tts });
        break;
      }
      case 'done': {
        dispatch({
          action: 'ai-done',
          ...msg,
          msgId,
        });
        break;
      }
      case 'error': {
        const { msgId, error } = msg;
        dispatch({ action: 'ai-error', msgId, error });
        break;
      }
    }
  });

  // handle socket state changes
  useEffect(() => {
    switch (socket.status) {
      case SOCKET_STATE.open: {
        dispatch({
          action: 'system-msg',
          status: SYSTEM_MSG_TYPE.socketConnected,
        });

        // loses context on reconnect. Inform user about this
        if (!IS_FIRST_TIME_CONNECTING) {
          dispatch({
            action: 'system-msg',
            status: SYSTEM_MSG_TYPE.contextReset,
          });
        }
        IS_FIRST_TIME_CONNECTING = false;
        break;
      }
      case SOCKET_STATE.closed: {
        dispatch({
          action: 'system-msg',
          status: SYSTEM_MSG_TYPE.socketDisconnected,
        });
        break;
      }
    }
  }, [socket.status]);

  // exported send message fn
  const actionSendMessage = useCallback(
    (text) => {
      const respMsgId = randId();
      dispatch({ action: 'send', text, respMsgId });
      socket.sendMessage({ type: 'query', text, msgId: respMsgId });
    },
    [dispatch, socket.sendMessage]
  );

  // exported ctxt reset fn
  const actionResetContext = useCallback(() => {
    dispatch({ action: 'system-msg', status: SYSTEM_MSG_TYPE.contextReset });
    socket.sendMessage({ type: 'reset-context' });
  }, [dispatch, socket.sendMessage]);

  return {
    state,
    actionSendMessage,
    actionResetContext,
  };
}
