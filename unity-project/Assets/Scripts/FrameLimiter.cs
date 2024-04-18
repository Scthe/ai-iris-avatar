using UnityEngine;

public class FrameLimiter : MonoBehaviour
{
  public int targetFrameRate = 30;

  [Tooltip("Show fps counter when running the app")]
  public bool showDuringRuntime = false;

  private int fontSize = 5;
  private int margin = 5;
  private float deltaTime = 0.0f;

  private void Start()
  {
    /// Does not always work, but worth a shot.
    /// https://discussions.unity.com/t/how-to-limit-fps/189237/4
    QualitySettings.vSyncCount = 0;
    Application.targetFrameRate = targetFrameRate;
    Debug.Log($"Trying FPS limit: {targetFrameRate}");
  }

  void Update()
  {
    deltaTime = Mathf.Lerp(deltaTime, Time.unscaledDeltaTime, 0.2f);
  }

  // some unity docs copied long time ago
  void OnGUI()
  {
    if (!showDuringRuntime) return;

    int w = Screen.width, h = Screen.height;

    GUIStyle style = new GUIStyle();

    Rect rect = new Rect(margin, margin, w, h * 2 / 100);
    style.alignment = TextAnchor.UpperLeft;
    style.fontSize = h * fontSize / 100;
    style.normal.textColor = Color.white;
    float ms = MyUtils.s2ms(deltaTime);
    float fps = 1.0f / deltaTime;
    string text = string.Format("{0:0.0} ms ({1:0.} fps)", ms, fps);
    GUI.Label(rect, text, style);
  }
}