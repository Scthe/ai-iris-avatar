import { useCallback, useState, useEffect } from 'https://esm.sh/preact/hooks';

import { useLatest } from './utils.mjs';
import { SOCKET_STATE } from './constants.mjs';
import { getSoundManager } from './sound_manager.mjs';

const getAudioContext = () => {
  if (!window.myAudioCtx) {
    window.myAudioCtx = new AudioContext();
  }
  return window.myAudioCtx;
};

export function useSocket(url, onMessage) {
  const [status, setStatus] = useState(SOCKET_STATE.connecting);
  const [socket, setSocket] = useState(undefined); // TODO [low] handle url change (NOPE!)
  const onMessageRef = useLatest(onMessage);

  const reloadSocket = useCallback(() => {
    const socket = new WebSocket(url);
    socket.addEventListener('open', () => {
      setSocket(socket);
      setStatus(SOCKET_STATE.open);
    });

    socket.addEventListener('message', async (event) => {
      if (event.data instanceof Blob) {
        console.log('Audio data:', event);
        const wav = event.data;
        // const audioEl = document.getElementById('audio');
        // audioEl.src = URL.createObjectURL(wav);
        // audioEl.hidden = false;

        const sm = getSoundManager();
        sm.addChunk(wav);
        /*
        let reader = new FileReader();
        reader.readAsArrayBuffer(wav);
        reader.onload = async () => {
          let arrayBuffer = reader.result;
          // let audioBuffer = await context.decodeAudioData(arrayBuffer)
          // console.log(audioBuffer) // ???

          const audioContext = getAudioContext();
          const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
          const source = audioContext.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(audioContext.destination);
          source.start();

          // const mediaSource = new MediaSource();
          // const sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg');
          // audioEl.src = URL.createObjectURL(mediaSource);
          // sourceBuffer.appendBuffer(arrayBuffer); // Repeat this for each chunk as ArrayBuffer
          // audioEl.play();
        };
        */
      } else {
        const msg = JSON.parse(event.data);
        console.log('Socket rcv ', msg);
        onMessageRef.current?.(msg);
      }
    });

    socket.addEventListener('close', () => {
      console.log('Socket closed.');
      setStatus(SOCKET_STATE.closed);
      setSocket(undefined);
    });
    return socket;
  }, []);

  useEffect(() => {
    const socket = reloadSocket();

    return () => {
      socket?.close();
      setSocket(undefined);
    };
  }, [reloadSocket]);

  const sendMessage = useCallback((msg) => {
    console.log('Socket sending ', msg);
    socket?.send(JSON.stringify(msg));
  });

  const reconnect = useCallback(() => {
    if (status === SOCKET_STATE.closed && !socket) {
      console.log('Reconnecting..');
      setStatus(SOCKET_STATE.connecting);
      reloadSocket();
    } else {
      console.log('No need for reconnect', { status, socket });
    }
  }, [status, socket]);

  return { status, sendMessage, reconnect };
}
