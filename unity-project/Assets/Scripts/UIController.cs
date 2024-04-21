using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UIElements;

enum PanelDisplayMode
{
  Input, Connecting, Reconnect
}


/// Tutorial:
/// https://www.youtube.com/watch?v=QjHW9ohdxyw&list=PLgCVPIIZ3xL_FVLhDrC3atsy8CiZzAMh6&index=2
public class UIController : MonoBehaviour
{
  public WebSocketClientBehaviour webSocketClient;

  private static readonly int CURSOR_BLINK_FREQ = 1000;

  private VisualElement chatWrapperEl;
  private VisualElement modeInputEl;
  private VisualElement modeReconnectEl;
  private VisualElement modeConnectingEl;

  private TextField textInputEl;
  private Label placeholderEl;
  private Button sendBtnEl;
  private Button reconnectBtnEl;

  void Start()
  {
    var root = GetComponent<UIDocument>().rootVisualElement;
    chatWrapperEl = root.Q<VisualElement>("ChatWrapper");
    modeInputEl = root.Q<VisualElement>("InputMode");
    modeReconnectEl = root.Q<VisualElement>("ReconnectMode");
    modeConnectingEl = root.Q<VisualElement>("ConnectingMode");

    textInputEl = root.Q<TextField>("ChatInput");
    placeholderEl = root.Q<Label>("Placeholder");
    sendBtnEl = root.Q<Button>("SendButton");
    reconnectBtnEl = root.Q<Button>("ReconnectButton");

    sendBtnEl.RegisterCallback<ClickEvent>(OnSendBtnClick);
    textInputEl.RegisterCallback<ChangeEvent<string>>(OnTextInputChanged);
    textInputEl.RegisterCallback<KeyDownEvent>(OnTextInputKeyDown);
    reconnectBtnEl.RegisterCallback<ClickEvent>(OnReconnectBtnClick);

    // focus colors
    textInputEl.RegisterCallback<FocusInEvent>(e =>
    {
      // Debug.Log("Focus in");
      SetChatWrapperFocused(true);
    });
    textInputEl.RegisterCallback<FocusOutEvent>(e =>
    {
      // Debug.Log("Focus out");
      SetChatWrapperFocused(false);
    });

    SetTextInputValue("");
    BlinkingCursor(textInputEl);
    ApplyPanelMode(PanelDisplayMode.Connecting);

    webSocketClient?.onConnectionChanged.AddListener(this.OnWebsocketConnectionStateChange);
  }

  public void OnWebsocketConnectionStateChange(WebSocketClientBehaviour _ws, WebSocketConnectionState state)
  {
    // Debug.Log($"Detected change: {state}");
    switch (state)
    {
      case WebSocketConnectionState.Ok:
        {
          ApplyPanelMode(PanelDisplayMode.Input);
          break;
        }
      case WebSocketConnectionState.Connecting:
        {
          ApplyPanelMode(PanelDisplayMode.Connecting);
          break;
        }
      case WebSocketConnectionState.NotConnected:
        {
          ApplyPanelMode(PanelDisplayMode.Reconnect);
          break;
        }
    }
  }

  async private void sendQueryToServer()
  {
    var query = textInputEl.text;
    if (string.IsNullOrEmpty(query)) { return; }

    SetTextInputValue("");
    await webSocketClient?.SendQuery(query);
  }

  private void SetTextInputValue(string value)
  {
    textInputEl.value = value;
    // UpdatePlaceholder(value);
  }

  private void ApplyPanelMode(PanelDisplayMode mode)
  {
    Action<VisualElement> show = el => el.style.display = DisplayStyle.Flex;
    Action<VisualElement> hide = el => el.style.display = DisplayStyle.None;

    switch (mode)
    {
      case PanelDisplayMode.Input:
        {
          show(modeInputEl);
          hide(modeReconnectEl);
          hide(modeConnectingEl);
          break;
        }
      case PanelDisplayMode.Connecting:
        {
          hide(modeInputEl);
          hide(modeReconnectEl);
          show(modeConnectingEl);
          break;
        }
      case PanelDisplayMode.Reconnect:
        {
          hide(modeInputEl);
          show(modeReconnectEl);
          hide(modeConnectingEl);
          break;
        }
    }

    SetChatWrapperFocused(false);
  }

  // -------------------------------
  // CALLBACKS BELOW

  private void OnReconnectBtnClick(ClickEvent e)
  {
    Debug.Log("Reconnect clicked");
    webSocketClient?.Reconnect();
  }

  private void OnSendBtnClick(ClickEvent e)
  {
    sendQueryToServer();
  }

  private void OnTextInputChanged(ChangeEvent<string> e)
  {
    // UpdatePlaceholder(e.newValue);
  }

  private void OnTextInputKeyDown(KeyDownEvent e)
  {
    // TODO other suff that does not have enter? Nope, peasants, use the send button
    // Debug.Log(e.keyCode);
    if (e.keyCode == KeyCode.Return)
    {
      sendQueryToServer();
    }
  }

  private void SetChatWrapperFocused(bool focused)
  {
    var className = "chat-wrapper-focused";
    if (focused)
    {
      chatWrapperEl.AddToClassList(className);
      // chatWrapperEl.style.backgroundColor = Color.red;
      UpdatePlaceholder("hidden"); // hide placeholder
    }
    else
    {
      chatWrapperEl.RemoveFromClassList(className);
      UpdatePlaceholder(""); // show placeholder
    }
  }

  private void UpdatePlaceholder(string nextInputVal)
  {
    placeholderEl.style.display = string.IsNullOrEmpty(nextInputVal) ?
    DisplayStyle.Flex : DisplayStyle.None;
  }

  public static void BlinkingCursor(TextField tf)
  {
    tf.schedule.Execute(() =>
    {
      // Debug.Log("Check classes: " + tf.ClassListContains("transparentCursor"));
      if (tf.ClassListContains("transparentCursor"))
        tf.RemoveFromClassList("transparentCursor");
      else
        tf.AddToClassList("transparentCursor");
    }).Every(UIController.CURSOR_BLINK_FREQ);
  }
}
