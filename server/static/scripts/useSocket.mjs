import { useCallback, useState, useEffect } from 'https://esm.sh/preact/hooks';

import { useLatest } from './utils.mjs';
import { SOCKET_STATE } from './constants.mjs';

export function useSocket(url, onMessage) {
  const [status, setStatus] = useState(SOCKET_STATE.connecting);
  const [socket, setSocket] = useState(undefined); // TODO [low] handle url change (NOPE!)
  const onMessageRef = useLatest(onMessage);

  // util to create new connection
  const reloadSocket = useCallback(() => {
    const socket = new WebSocket(url);
    socket.addEventListener('open', () => {
      setSocket(socket);
      setStatus(SOCKET_STATE.open);
    });

    // on incoming message
    socket.addEventListener('message', async (event) => {
      const msg = JSON.parse(event.data);
      console.log('Socket rcv ', msg);
      onMessageRef.current?.(msg);
    });

    // on disconnect
    socket.addEventListener('close', () => {
      console.log('Socket closed.');
      setStatus(SOCKET_STATE.closed);
      setSocket(undefined);
    });
    return socket;
  }, []);

  // initial connect
  useEffect(() => {
    const socket = reloadSocket();

    return () => {
      socket?.close();
      setSocket(undefined);
    };
  }, [reloadSocket]);

  // exported fn to send new message
  const sendMessage = useCallback((msg) => {
    console.log('Socket sending ', msg);
    socket?.send(JSON.stringify(msg));
  });

  // exported fn to reconnect
  const reconnect = useCallback(() => {
    if (status === SOCKET_STATE.closed && !socket) {
      console.log('Reconnecting..');
      setStatus(SOCKET_STATE.connecting);
      reloadSocket();
    } else {
      console.log('No need for reconnect', { status, socket });
    }
  }, [status, socket]);

  // exports
  return { status, sendMessage, reconnect };
}
