using UnityEngine;

/// Does not always work, but worth a shot.
/// https://discussions.unity.com/t/how-to-limit-fps/189237/4
public class FrameLimiter : MonoBehaviour
{
  public int targetFrameRate = 30;

  private void Start()
  {
    QualitySettings.vSyncCount = 0;
    Application.targetFrameRate = targetFrameRate;
    Debug.Log($"Trying FPS limit: {targetFrameRate}");
  }
}