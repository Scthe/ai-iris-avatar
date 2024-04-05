using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// TODO in proper anim system this moves face muscles too

public class EyesFollowCameraController : MonoBehaviour
{
  public Transform leftEyeBone = null;
  public Transform rightEyeBone = null;
  public float updateInterval = 1.0f;


  [Header("Look at target")]
  public GameObject target = null;
  public Vector3 targetOffset = Vector3.zero;

  private Vector3 initialEyeRotationLeft;
  private Vector3 initialEyeRotationRight;

  void Start()
  {
    initialEyeRotationLeft = leftEyeBone.localEulerAngles;
    initialEyeRotationRight = rightEyeBone.localEulerAngles;

    if (target == null)
    {
      target = Camera.main.gameObject;
    }

    StartCoroutine(UpdateEyesOnInterval());
  }



  IEnumerator UpdateEyesOnInterval()
  {
    while (true)
    {
      yield return wait(updateInterval);
      ApplyEyesLookAt();
    }
  }


  void ApplyEyesLookAt()
  {
    var t = target.transform.TransformPoint(Vector3.zero) + targetOffset;

    var leftEyeWS = leftEyeBone.TransformPoint(Vector3.zero);
    var rightEyeWS = rightEyeBone.TransformPoint(Vector3.zero);
    var leftToRightVector = rightEyeWS - leftEyeWS;

    // This assumes that by default the character looks at the target. Fine for this simple demo.
    leftEyeBone.LookAt(t - leftToRightVector / 2f);
    leftEyeBone.localEulerAngles += initialEyeRotationLeft;
    rightEyeBone.LookAt(t + leftToRightVector / 2f);
    rightEyeBone.localEulerAngles += initialEyeRotationRight;
  }

  /// TODO copied from BlinkController, move to utils
  IEnumerator wait(float waitTimeSeconds)
  {
    float passedTime = 0;

    while (passedTime < waitTimeSeconds)
    {
      passedTime += Time.deltaTime; // is float (in seconds)
      yield return null;
    }
  }
}
