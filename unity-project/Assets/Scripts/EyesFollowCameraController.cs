using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// TODO in proper anim system this moves face muscles too

// NOTE Let's just say that this script has some.. problems

public class EyesFollowCameraController : MonoBehaviour
{
  public Transform leftEyeBone = null;
  public Transform rightEyeBone = null;
  public float updateInterval = 1.0f;

  [Tooltip("Minimal angle (in dgr) that will cause update")]
  [Range(0.0f, 90.0f)]
  public float minDeltaAngle = 2.0f;

  [Header("Look at target")]
  public GameObject target = null;
  public Vector3 targetOffset = Vector3.zero; // 0, 0.065, 0

  private Vector3 initialEyeRotationLeft;
  private Vector3 initialEyeRotationRight;

  private Vector3 lastToTarget = Vector3.zero;

  void Start()
  {
    initialEyeRotationLeft = leftEyeBone.localEulerAngles;
    initialEyeRotationRight = rightEyeBone.localEulerAngles;
    // Debug.Log($"initialEyeRotationRight= {initialEyeRotationRight}");

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
      ApplyEyesLookAt();
      yield return MyUtils.wait(updateInterval);
    }
  }


  void ApplyEyesLookAt()
  {
    var target = this.target.transform.TransformPoint(Vector3.zero) + targetOffset;
    // var t = new Vector3(0f, 1.775f, -10);
    // var t = new Vector3(0f, 10f, -10f);

    var leftEyeWS = leftEyeBone.TransformPoint(Vector3.zero);
    var rightEyeWS = rightEyeBone.TransformPoint(Vector3.zero);
    var middleWS = (leftEyeWS + rightEyeWS) / 2;
    var leftToRightVector = rightEyeWS - leftEyeWS;

    // var tfxBefore = rightEyeBone.rotation;
    // Debug.Log($"rightEyeBone.rotation 1: {tfxBefore}");

    if (hasMovedEnough(middleWS, target))
    {
      // This assumes that by default the character looks at the target. Fine for this simple demo.
      leftEyeBone.LookAt(target - leftToRightVector / 2f);
      leftEyeBone.localEulerAngles += initialEyeRotationLeft;
      rightEyeBone.LookAt(target + leftToRightVector / 2f);
      rightEyeBone.localEulerAngles += initialEyeRotationRight;
    }


    // var tfxAfter = rightEyeBone.rotation;
    // Debug.Log($"rightEyeBone.rotation 2: {tfxAfter}");
    // var angleCos = Quaternion.Angle(tfxBefore, tfxAfter);
    // Debug.Log($"OK ANGLE: {angleCos}dgr");
  }

  private bool hasMovedEnough(Vector3 middle, Vector3 target)
  {
    // var middle = (rightEyeBone.position + leftEyeBone.position) / 2; // hmm...
    var toTarget = (target - middle).normalized;
    var tmp = this.lastToTarget;

    if (MyUtils.IsCloseToZero(tmp))
    {
      this.lastToTarget = toTarget;
      return true;
    }

    var angle = Vector3.Angle(toTarget, tmp);
    // Debug.Log("Eyes delta angle: " + (angle) + "dgr");
    if (angle >= minDeltaAngle)
    {
      this.lastToTarget = toTarget;
      return true;
    }

    return false;
  }
}
