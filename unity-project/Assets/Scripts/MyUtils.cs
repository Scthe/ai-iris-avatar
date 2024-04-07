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

  public static bool IsCloseToZero(this Vector3 vec, float sqrEpsilon = 1E-5f)
    => vec.sqrMagnitude < sqrEpsilon;

}
