using System.Collections;
using System.Collections.Generic;
using UnityEngine;


/// <summary>
/// Small controller to easier position camera in debug builds.
/// Prod build shoud use static camera.
/// </summary>
[RequireComponent(typeof(Camera))]
public class CameraController : MonoBehaviour
{
  public float speed = 1.0f;
  public float shiftSpeed = 2.0f;
  public float mouseSensitivity = 0.25f;
  private Vector3 lastMouse = new Vector3(255, 255, 255); //kind of in the middle of the screen, rather than at the top (play)


  void Update()
  {
    if (MyUtils.IsDebugRelease)
    {
      UpdateRotationFreeCamera();
      UpdatePositionFreeCamera();
    }
  }

  private void UpdateRotationFreeCamera()
  {
    if (Input.GetMouseButton(0))
    {
      var delta = Input.mousePosition - lastMouse;
      delta = new Vector3(-delta.y * mouseSensitivity, delta.x * mouseSensitivity, 0);
      transform.eulerAngles = new Vector3(
        transform.eulerAngles.x + delta.x,
        transform.eulerAngles.y + delta.y,
        0
      );
    }
    lastMouse = Input.mousePosition;
  }

  private void UpdatePositionFreeCamera()
  {
    Vector3 move = GetMoveVectorFrom_WSAD();
    if (move.sqrMagnitude > 0)
    {
      var camera = GetComponent<Camera>();
      var speed2 = Input.GetKey(KeyCode.LeftShift) ? shiftSpeed : speed;
      move *= speed2 * Time.deltaTime;

      if (camera.orthographic)
      {
        camera.orthographicSize += -0.5f * move.z;
        move.z = 0;
      }
      transform.Translate(move);
    }
  }

  private Vector3 GetMoveVectorFrom_WSAD()
  {
    Vector3 move = new Vector3();
    if (Input.GetKey(KeyCode.W))
    {
      move += Vector3.forward;
    }
    if (Input.GetKey(KeyCode.S))
    {
      move += Vector3.back;
    }
    if (Input.GetKey(KeyCode.A))
    {
      move += Vector3.left;
    }
    if (Input.GetKey(KeyCode.D))
    {
      move += Vector3.right;
    }
    if (Input.GetKey(KeyCode.Space))
    {
      move += Vector3.up;
    }
    if (Input.GetKey(KeyCode.Z))
    {
      move += Vector3.down;
    }
    return move;
  }
}
