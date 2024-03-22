export const getSoundManager = () => {
  if (!window.mySoundManager) {
    const ctx = new AudioContext();
    window.mySoundManager = new SoundManager(ctx);
  }
  return window.mySoundManager;
};

/**
 * TL;DR: Web Audio API sucks.
 *
 * https://stackoverflow.com/questions/37459231/webaudio-seamlessly-playing-sequence-of-audio-chunks
 * https://github.com/scottstensland/websockets-streaming-audio/blob/master/src/ww_client_socket.js
 *
 *
 * ## Other:
 * - https://github.com/WebAudio/web-audio-api/issues/1825
 * - https://github.com/kmoskwiak/node-tcp-streaming-server/blob/master/client/js/app.js
 * - https://github.com/anthumchris/fetch-stream-audio/blob/master/src/js/modules/audio-stream-player.mjs
 * - https://github.com/Honghe/demo_fastapi_websocket/blob/master/src/static/js/main.js#L42
 * - https://github.com/agektmr/AudioStreamer/blob/master/public/js/AudioStreamer.js
 * - https://stackoverflow.com/questions/47600421/web-audio-api-proper-way-to-play-data-chunks-from-a-nodejs-server-via-socket
 */
export class SoundManager {
  constructor(ctx) {
    this.ctx = ctx;
    // this.gainNode = ctx.createGain();
    // this.gainNode.connect(ctx.destination); // TODO (volume control) connect below, add ui

    this.chunks = [];
    this.isPlaying = false;
    this.startTime = 0;
    this.lastChunkOffset = 0;
  }

  log(data) {
    if (this.debug) {
      console.log(new Date().toUTCString() + ' : ' + data);
    }
  }

  async addChunk(data) {
    if (this.isPlaying) {
      // schedule & add right now
      this.log('chunk accepted');
      let chunk = await this._createChunk(data);
      chunk.start(this.startTime + this.lastChunkOffset);
      this.lastChunkOffset += chunk.buffer.duration;
      this.chunks.push(chunk);
    } else {
      // add & schedule entire buffer
      this.log('queued chunks scheduled');
      this.isPlaying = true;
      let chunk = await this._createChunk(data);
      this.chunks.push(chunk);
      this.startTime = this.ctx.currentTime;
      this.lastChunkOffset = 0;
      for (let i = 0; i < this.chunks.length; i++) {
        let chunk = this.chunks[i];
        chunk.start(this.startTime + this.lastChunkOffset);
        this.lastChunkOffset += chunk.buffer.duration;
      }
    }
  }

  async _createChunk(chunk) {
    const audioContext = this.ctx;
    // var audioBuffer = this.ctx.createBuffer(2, chunk.length, this.sampleRate);
    // audioBuffer.getChannelData(0).set(chunk);
    const arrayBuffer = await toArrayBuffer(chunk);
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);

    source.onended = (_e) => {
      this.chunks.splice(this.chunks.indexOf(source), 1);
      if (this.chunks.length == 0) {
        this.isPlaying = false;
        this.startTime = 0;
        this.lastChunkOffset = 0;
      }
    };
    return source;
  }
}

function toArrayBuffer(wav) {
  return new Promise((res) => {
    let reader = new FileReader();
    reader.readAsArrayBuffer(wav);
    reader.onload = async () => {
      res(reader.result);
    };
  });
}
