using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;


public static class MyUtils
{

  public static IEnumerator wait(float waitTimeSeconds)
  {
    float passedTime = 0;

    while (passedTime < waitTimeSeconds)
    {
      passedTime += Time.deltaTime; // is float (in seconds)
      yield return null;
    }
  }

  /// seconds to miliseconds
  public static float s2ms(float seconds)
  {
    return seconds * 1000f;
  }

  /// miliseconds to seconds
  public static float ms2s(float miliseconds)
  {
    return miliseconds / 1000f;
  }

  /// Timestamp string: HH:mm:ss
  public static string ts_str()
  {
    return System.DateTime.UtcNow.ToString("HH:mm:ss");
  }

  public static bool IsCloseToZero(this Vector3 vec, float sqrEpsilon = 1E-5f)
    => vec.sqrMagnitude < sqrEpsilon;

  public static void SafeSetBlendShapeWeight(
    SkinnedMeshRenderer skinnedMesh,
    string blendShapeName,
    float value
    )
  {
    if (skinnedMesh == null) { return; }

    var mesh = skinnedMesh.sharedMesh;
    var blendShapeIdx = mesh.GetBlendShapeIndex(blendShapeName);

    if (blendShapeIdx != -1 && blendShapeIdx < mesh.blendShapeCount)
    {
      skinnedMesh.SetBlendShapeWeight(blendShapeIdx, value * 100.0f);
    }
  }

  public static bool IsDebugRelease
  {
    get
    {
#if DEBUG
      return true;
#else
      return false;
#endif
    }
  }
}
