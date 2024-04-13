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
  public float updateInterval = 1.3f;

  [Tooltip("Minimal angle (in dgr) that will cause update")]
  [Range(0.0f, 90.0f)]
  public float minDeltaAngle = 2.0f;

  [Header("Look at target")]
  public Transform target = null;

  [Tooltip("Draw debug shapes")]
  public bool debug = false;

  private Vector3 lastToTarget = Vector3.zero;
  private Quaternion LOCAL_ROT_QUAT;
  private float angleBetweenEyeAndTarget = 0f;

  void Start()
  {
    // Debug.Log($"initialEyeRotationRight= {leftEyeBone.localEulerAngles}");

    // somehow the bone has Unity's forward pointing down. Messes up look at etc.
    LOCAL_ROT_QUAT = Quaternion.AngleAxis(90f, new Vector3(1.0f, 0f, 0f));
    // custom fix to raise pupils a bit. We could have rotated once (by 85dgr),
    // but this is easier to explain.
    LOCAL_ROT_QUAT *= Quaternion.AngleAxis(-7f, new Vector3(1.0f, 0f, 0f));

    if (target == null)
    {
      target = Camera.main.gameObject.transform;
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
    var target = this.target.position;

    var leftEyeWS = leftEyeBone.position;
    var rightEyeWS = rightEyeBone.position;
    var middleWS = (leftEyeWS + rightEyeWS) / 2;
    var leftToRightVector = rightEyeWS - leftEyeWS;

    if (HasMovedEnough(middleWS, target))
    {
      // This assumes that by default the character looks at the target. Fine for this simple demo.
      leftEyeBone.LookAt(target - leftToRightVector / 2f);
      rightEyeBone.LookAt(target + leftToRightVector / 2f);
      leftEyeBone.localRotation *= LOCAL_ROT_QUAT;
      rightEyeBone.localRotation *= LOCAL_ROT_QUAT;
    }

    /*
    var dirBetweenEyesToTarget = (target - middleWS).normalized;
    Quaternion expectedRotation = Quaternion.LookRotation(dirBetweenEyesToTarget, Vector3.up);
    angleBetweenEyeAndTarget = Quaternion.Angle(leftEyeBone.rotation, expectedRotation);// - LOCAL_EULER_INNITIAL[0];
    // if (angleBetweenEyeAndTarget >= minDeltaAngle)
    // {
    // Debug.Log($"Angle: {angleBetweenEyeAndTarget}");
    leftEyeBone.rotation = expectedRotation;
    rightEyeBone.rotation = expectedRotation;
    leftEyeBone.localRotation *= LOCAL_ROT_QUAT;
    rightEyeBone.localRotation *= LOCAL_ROT_QUAT;
    // }
    */

    // var tfxAfter = rightEyeBone.rotation;
    // Debug.Log($"rightEyeBone.rotation 2: {tfxAfter}");
    // var angleCos = Quaternion.Angle(tfxBefore, tfxAfter);
    // Debug.Log($"OK ANGLE: {angleCos}dgr");
  }

  private bool HasMovedEnough(Vector3 betweenEyes, Vector3 target)
  {
    // var middle = (rightEyeBone.position + leftEyeBone.position) / 2; // hmm...
    var toTarget = (target - betweenEyes).normalized;
    var tmp = this.lastToTarget;

    if (MyUtils.IsCloseToZero(tmp))
    {
      this.lastToTarget = toTarget;
      return true;
    }

    angleBetweenEyeAndTarget = Vector3.Angle(toTarget, tmp);
    // Debug.Log("Eyes delta angle: " + (angle) + "dgr");
    if (angleBetweenEyeAndTarget >= minDeltaAngle)
    {
      this.lastToTarget = toTarget;
      return true;
    }

    return false;
  }

  private Vector3 GetTargetsPerEye(out Vector3 outLeft, out Vector3 outRight)
  {
    var target = this.target.transform.position;
    var leftEyeWS = leftEyeBone.position;
    var rightEyeWS = rightEyeBone.position;
    var leftToRightVector = rightEyeWS - leftEyeWS;
    outLeft = target - (leftToRightVector / 2f);
    outRight = target + (leftToRightVector / 2f);
    return target;
  }

  private void OnDrawGizmos()
  {
    if (!debug) return;

    Vector3 leftEyeTarget, rightEyeTarget;
    var target = GetTargetsPerEye(out leftEyeTarget, out rightEyeTarget);

    Gizmos.color = Color.yellow; // target
    Gizmos.DrawWireSphere(target, 0.02f);
    Gizmos.color = Color.magenta; // per-eye targets
    Gizmos.DrawWireSphere(leftEyeTarget, 0.01f);
    Gizmos.DrawWireSphere(rightEyeTarget, 0.01f);

    Gizmos.color = Color.red; // current look direction
    // Vector3 direction = this.target.TransformDirection(Vector3.forward);
    Vector3 direction = leftEyeBone.rotation * Vector3.up;
    direction = direction.normalized * 0.1f;
    Gizmos.DrawRay(leftEyeBone.position, direction);
    direction = rightEyeBone.rotation * Vector3.up;
    direction = direction.normalized * 0.1f;
    Gizmos.DrawRay(rightEyeBone.position, direction);

    Gizmos.color = Color.yellow; // to target
    var middleWS = (leftEyeBone.position + rightEyeBone.position) / 2f;
    // var v0 = (leftEyeBone.rotation * Vector3.up).normalized;
    direction = (leftEyeTarget - leftEyeBone.position).normalized;
    Gizmos.DrawRay(leftEyeBone.position, direction);
    direction = (rightEyeTarget - rightEyeBone.position).normalized;
    Gizmos.DrawRay(rightEyeBone.position, direction);
  }

  void OnGUI()
  {
    if (!debug) return;

    int w = Screen.width, h = Screen.height;

    GUIStyle style = new GUIStyle();

    Rect rect = new Rect(0, 0, w, h * 2 / 100);
    style.alignment = TextAnchor.UpperLeft;
    style.fontSize = h * 2 / 100;
    string text = string.Format($"EyeAngle: {angleBetweenEyeAndTarget}");
    GUI.Label(rect, text, style);
  }
}
