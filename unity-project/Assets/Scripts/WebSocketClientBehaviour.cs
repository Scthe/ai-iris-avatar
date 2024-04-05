using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using NativeWebSocket;

// https://github.com/endel/NativeWebSocket

[Serializable]
public class SocketMsg
{
  public string type;
  public string text;
}


public class WebSocketClientBehaviour : MonoBehaviour
{
  [Tooltip("Address of the Python sever e.g. 'ws://localhost:8080'.")]
  public string websocketEndpoint = "ws://localhost:8080";

  [Tooltip("Disable WebSocket. Use when e.g. testing with unity file.")]
  public bool disableWebsocket = false;

  [Tooltip("Object that has AudioSource component. We will use this object to play the sounds.")]
  public GameObject targetObject;

  WebSocket websocket;
  AudioSource audioComponent;

  // Start is called before the first frame update
  async void Start()
  {
    if (!disableWebsocket)
    {
      InitWebSocket();
      if (websocket != null)
      {
        // Keep sending messages at every 0.3s
        // InvokeRepeating("SendWebSocketMessage", 0.0f, 2.0f);

        // waiting for messages
        await websocket.Connect();
      }
    }
  }

  void InitWebSocket()
  {
    websocket = new WebSocket(this.websocketEndpoint);

    websocket.OnOpen += OnConnectionOpen;

    websocket.OnError += (e) =>
    {
      Debug.Log("Error! " + e);
    };

    websocket.OnClose += (e) =>
    {
      Debug.Log("Connection closed!");
    };

    websocket.OnMessage += OnMessage;
  }

  void Awake()
  {
    if (!disableWebsocket)
    {
      this.CacheAudioSourceRef();
    }
    this.DebugBlendShapes();
  }

  private void CacheAudioSourceRef()
  {
    audioComponent = null;
    if (targetObject)
    {
      audioComponent = targetObject.GetComponent<AudioSource>();
      Debug.Log(audioComponent);
    }

    if (!audioComponent)
    {
      Debug.Log("[WebSocketClientBehaviour] Could not get reference to target's AudioSource component");
    }
  }

  private void DebugBlendShapes()
  {
    // https://docs.unity3d.com/ScriptReference/SkinnedMeshRenderer.html
    var skinnedMeshRenderer = targetObject?.GetComponent<SkinnedMeshRenderer>();
    // https://docs.unity3d.com/ScriptReference/Mesh.html
    var skinnedMesh = skinnedMeshRenderer?.sharedMesh;

    List<string> blendShapes = new List<string>(skinnedMesh.blendShapeCount);
    for (int i = 0; i < skinnedMesh.blendShapeCount; i++)
    {
      blendShapes.Add(skinnedMesh.GetBlendShapeName(i));
    }

    Debug.Log("Blendshape count: " + skinnedMesh.blendShapeCount);
    foreach (var item in blendShapes)
    {
      Debug.Log("Blendshape: " + item);
    }
  }


  void Update()
  {
#if !UNITY_WEBGL || UNITY_EDITOR
    if (websocket != null)
    {
      websocket.DispatchMessageQueue();
    }
#endif
  }

  /*
  async void SendWebSocketMessage()
  {
    if (websocket.State == WebSocketState.Open)
    {
      // Sending bytes
      // await websocket.Send(new byte[] { 10, 20, 30 });

      // Sending plain text
      await websocket.SendText("{\"value\":\"plain text message\"}");
    }
  }
  */

  async void OnConnectionOpen()
  {
    Debug.Log("Connection open!");
    SocketMsg msg = new SocketMsg();
    msg.type = "query";
    msg.text = "Michael Jordan is an American collegiate and professional basketball player widely considered to be one of the greatest all-around players in the history of the game. He led the Chicago Bulls to six National Basketball Association (NBA) championships.";
    string json = JsonUtility.ToJson(msg);

    await websocket.SendText(json);
  }

  void OnMessage(byte[] bytes)
  {
    Debug.Log("OnMessage!");
    // Debug.Log(bytes);

    // getting the message as a string
    // var message = System.Text.Encoding.UTF8.GetString(bytes);
    // Debug.Log("OnMessage! " + message);

    SpeakWavFile(bytes);
  }

  private void SpeakWavFile(byte[] bytes)
  {
    var pcmData = PcmData.FromBytes(bytes);
    var audioClip = AudioClip.Create("pcm", pcmData.Length, pcmData.Channels, pcmData.SampleRate, false);
    audioClip.SetData(pcmData.Value, 0);

    if (audioComponent)
    {
      audioComponent.clip = audioClip;
      audioComponent.Play();
    }
  }

  private async void OnApplicationQuit()
  {
    if (websocket != null)
    {
      await websocket.Close();
    }
  }

}
