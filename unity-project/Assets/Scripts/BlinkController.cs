using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using static MyUtils;

/// <summary>
/// Blinking animation guide: https://www.youtube.com/watch?v=c0DimVO18ps
/// <br /><br />
/// - TODO move pupil and cornea down too
/// </summary>
public class BlinkController : MonoBehaviour
{

  [Header("Meshes")]
  [Tooltip("Object to animate")]
  public SkinnedMeshRenderer bodyMesh = null;
  [Tooltip("Eyelashes mesh that have 'eyelidsDown' shape key")]
  public SkinnedMeshRenderer eyelashesMesh = null;

  // EYELIDS DOWN
  [Tooltip("Strength of 'eyelids down' shape key when idle")]
  [Range(0.0f, 1.0f)]
  public float IdleEyelidsDown = 0.0f;
  private readonly string SK_EYELIDS_DOWN = "eyelidsDown";

  // EYEBROWS DOWN
  [Header("Shape keys")]
  [Tooltip("Strength of 'eyebrows down' shape key")]
  [Range(0.0f, 1.0f)]
  public float EyebrowsDownStr = 0.529f;
  private readonly string SK_BROW_DOWN_L = "BROW-mad.L";
  private readonly string SK_BROW_DOWN_R = "BROW-mad.R";


  // EYEBROWS CORNERS DOWN
  [Tooltip("Strength of 'eyebrows inner corner up' shape key")]
  [Range(0.0f, 1.0f)]
  public float EyebrowsCornerUpStr = 0.05f;
  private readonly string SK_BROW_CORNER_UP_L = "BROW-surp.L";
  private readonly string SK_BROW_CORNER_UP_R = "BROW-surp.R";


  // SQUINTING
  [Tooltip("Strength of 'eye squint' shape key")]
  [Range(0.0f, 1.0f)]
  public float SquintStr = 0.6f;
  private readonly string SK_SQUINT_L = "EYE-squint.L";
  private readonly string SK_SQUINT_R = "EYE-squint.R";


  // TIMINGS
  [Header("Timings")]
  [Tooltip("Shortest possible time between blinks (in seconds). Usually 1s.")]
  [Range(0.1f, 10.0f)]
  public float BlinkIntervalMin = 1.0f;
  [Tooltip("Longest possible time between blinks (in seconds). Usually 5s.")]
  [Range(0.1f, 10.0f)]
  public float BlinkIntervalMax = 4.0f; // 5.0f is more natural, but short demo so..
  [Tooltip("Duration of the single blink (in seconds). Usually 0.2s.")]
  public float BlinkDuration = 0.2f; // 200ms

  public AnimationCurve blinkDownInterpolationCurve = AnimationCurve.EaseInOut(0f, 0f, 0f, 0f);
  public AnimationCurve blinkUpInterpolationCurve = AnimationCurve.EaseInOut(0f, 0f, 0f, 0f);


  void Start()
  {
    if (bodyMesh == null) { Debug.LogError("BlinkController: missing bodyMesh reference"); }
    if (eyelashesMesh == null) { Debug.LogError("BlinkController: missing eyelashesMesh reference"); }

    ClearBlinkShapeKeys();
    StartCoroutine(ExecuteBlinks());
  }

  void Awake()
  {
  }


  void Update()
  {
  }

  /// every 1000-5000ms, takes 200ms
  /// Async based on: https://stackoverflow.com/a/30065183
  IEnumerator ExecuteBlinks()
  {
    while (true)
    {
      var blinkInterval = UnityEngine.Random.Range(BlinkIntervalMin, BlinkIntervalMax);
      // Debug.LogFormat("Next blink in: {0:0.0}s", blinkInterval);
      yield return MyUtils.wait(blinkInterval);

      // See animation guide linked at the top of the file for guide for choosing timings
      // float[] keyframes = { 0.3f, 1.0f, 0.9f, 0.65f, 0.3f };
      float[] keyframes = {
        blinkDownInterpolationCurve.Evaluate(0.2f),
        // blinkDownInterpolationCurve.Evaluate(0.8f),
        blinkDownInterpolationCurve.Evaluate(0.9f),
        1.0f,
        // blinkUpInterpolationCurve.Evaluate(0.9f),
        blinkUpInterpolationCurve.Evaluate(0.8f),
        blinkUpInterpolationCurve.Evaluate(0.6f),
        // blinkUpInterpolationCurve.Evaluate(0.4f),
        blinkUpInterpolationCurve.Evaluate(0.3f),
        blinkUpInterpolationCurve.Evaluate(0.2f),
        blinkUpInterpolationCurve.Evaluate(0.1f),
      };
      var dt = BlinkDuration / keyframes.Length;
      foreach (float progress in keyframes)
      {
        ApplyBlinkShapeKeys(progress);
        yield return MyUtils.wait(dt);
      }

      ClearBlinkShapeKeys();
    }
  }

  void ApplyBlinkShapeKeys(float progress)
  {
    SafeSetBlendShapeWeight(bodyMesh, SK_BROW_DOWN_L, EyebrowsDownStr * progress);
    SafeSetBlendShapeWeight(bodyMesh, SK_BROW_DOWN_R, EyebrowsDownStr * progress);
    SafeSetBlendShapeWeight(bodyMesh, SK_BROW_CORNER_UP_L, EyebrowsCornerUpStr * progress);
    SafeSetBlendShapeWeight(bodyMesh, SK_BROW_CORNER_UP_R, EyebrowsCornerUpStr * progress);
    SafeSetBlendShapeWeight(bodyMesh, SK_SQUINT_L, SquintStr * progress);
    SafeSetBlendShapeWeight(bodyMesh, SK_SQUINT_R, SquintStr * progress);

    float eyelidsDownStr = Mathf.Lerp(IdleEyelidsDown, 1.0f, progress);
    SafeSetBlendShapeWeight(bodyMesh, SK_EYELIDS_DOWN, eyelidsDownStr);
    SafeSetBlendShapeWeight(eyelashesMesh, SK_EYELIDS_DOWN, eyelidsDownStr);
  }

  void ClearBlinkShapeKeys()
  {
    ApplyBlinkShapeKeys(0.0f);
  }
}
