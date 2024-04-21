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
  [Tooltip("Draw debug shapes")]
  public bool debug = false;

  [Header("Look at target")]
  public Transform target = null;


  [Header("Constraints")]
  [Range(-180.0f, 180.0f)]
  public float angleUp = 10f;
  [Range(-180.0f, 180.0f)]
  public float angleDown = 22f;
  [Range(-180.0f, 180.0f)]
  public float angleInside = 15f;
  [Range(-180.0f, 180.0f)]
  public float angleOutside = -28f;


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
      // average up/down rotation. Useful when head is not horizontal (one eye higher than other)
      float XRotation = (leftEyeBone.localEulerAngles[0] + rightEyeBone.localEulerAngles[0]) / 2f;

      // constraints
      XRotation = ApplyConstraintLocalRot_UpDown(XRotation);
      // Debug.Log($"rot: {leftEyeBone.localEulerAngles}, XRotation={XRotation}");
      // Debug.Log($"rot: {rightEyeBone.localEulerAngles}, XRotation={XRotation}");
      var YRotationL = ApplyConstraintLocalRot_SidesL();
      var YRotationR = ApplyConstraintLocalRot_SidesR();
      ApplyConstraint(leftEyeBone, XRotation, YRotationL);
      ApplyConstraint(rightEyeBone, XRotation, YRotationR);

      // Rotate 90dgr to fix axis_forward pointing down instead of forward
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

  private float ApplyConstraintLocalRot_UpDown(float angle)
  {
    return Mathf.Clamp(
       FixAngle(angle),
       Mathf.Min(angleUp, angleDown),
       Mathf.Max(angleUp, angleDown)
     );
  }

  private float ApplyConstraintLocalRot_SidesL()
  {
    return Mathf.Clamp(
        FixAngle(leftEyeBone.localEulerAngles[1]),
        Mathf.Min(angleInside, angleOutside),
        Mathf.Max(angleInside, angleOutside)
      );
  }

  private float ApplyConstraintLocalRot_SidesR()
  {
    return Mathf.Clamp(
        FixAngle(leftEyeBone.localEulerAngles[1]),
        Mathf.Min(-angleInside, -angleOutside),
        Mathf.Max(-angleInside, -angleOutside)
      );
  }

  private void ApplyConstraint(Transform tfxBone, float rotX, float rotY)
  {
    tfxBone.localRotation = Quaternion.Euler(
       rotX, rotY, tfxBone.localEulerAngles[2]
     );
  }

  private float FixAngle(float ang)
  {
    while (ang > 90f) ang -= 360f;
    return ang;
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

    Vector3 leftEyeTarget, rightEyeTarget, direction;
    var target = GetTargetsPerEye(out leftEyeTarget, out rightEyeTarget);

    // draw target + both eye_targets
    Gizmos.color = Color.yellow; // target
    Gizmos.DrawWireSphere(target, 0.02f);
    Gizmos.color = Color.magenta; // per-eye targets
    Gizmos.DrawWireSphere(leftEyeTarget, 0.01f);
    Gizmos.DrawWireSphere(rightEyeTarget, 0.01f);

    // Each eye: draw RED line based on tfx matrix
    Gizmos.color = Color.red; // current look direction
    direction = leftEyeBone.rotation * Vector3.up;
    direction = direction.normalized * 0.1f;
    Gizmos.DrawRay(leftEyeBone.position, direction);
    direction = rightEyeBone.rotation * Vector3.up;
    direction = direction.normalized * 0.1f;
    Gizmos.DrawRay(rightEyeBone.position, direction);

    // Each eye: draw YELLOW line from eye -> eye_target
    Gizmos.color = Color.yellow;
    direction = (leftEyeTarget - leftEyeBone.position).normalized;
    Gizmos.DrawRay(leftEyeBone.position, direction);
    direction = (rightEyeTarget - rightEyeBone.position).normalized;
    Gizmos.DrawRay(rightEyeBone.position, direction);

    // constraints
    Gizmos.color = Color.green;
    float[] constraintsY = { angleDown, -angleUp };
    foreach (var c in constraintsY)
    {
      var directionQ = leftEyeBone.rotation * Quaternion.AngleAxis(c, new Vector3(1.0f, 0f, 0f));
      direction = directionQ * Vector3.up;
      direction = direction.normalized * 0.1f;
      Gizmos.DrawRay(leftEyeBone.position, direction);
      Gizmos.DrawRay(rightEyeBone.position, direction);
    }

    // public float angleUp = 20f;
    // public float angleDown = 20f;
    // public float angleInside = 20f;
    // public float angleOutside = 20f;
  }

  void OnGUI()
  {
    if (!debug) return;

    int w = Screen.width, h = Screen.height;

    GUIStyle style = new GUIStyle();
    style.normal.textColor = Color.white;

    int hSize = h * 4 / 100;
    Rect rect = new Rect(0, 0, w, hSize);
    style.alignment = TextAnchor.UpperLeft;
    style.fontSize = hSize;
    string text = string.Format($"EyeAngle: {angleBetweenEyeAndTarget:F2}");
    GUI.Label(rect, text, style);
  }
}
