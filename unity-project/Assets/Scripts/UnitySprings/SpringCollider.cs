//
//SpringCollider for unity-chan!
//
//Original Script is here:
//ricopin / SpringCollider.cs
//Rocket Jump : http://rocketjump.skr.jp/unity3d/109/
//https://twitter.com/ricopin416
//
using UnityEngine;
using System.Collections;

namespace UnityChan
{
  // mm: pos: [0, -0.000283, 0.000748]
  public class SpringCollider : MonoBehaviour
  {
    //半径
    public float radius = 0.045f;
    [Tooltip("Draw collision sphere")]
    public bool debug = false;

    private void OnDrawGizmosSelected()
    {
      if (debug)
      {
        Gizmos.color = Color.green;
        Gizmos.DrawWireSphere(transform.position, radius);
      }
    }

    private void OnDrawGizmos()
    {
      if (debug)
      {
        Gizmos.color = Color.green;
        Gizmos.DrawWireSphere(transform.position, radius);
      }
    }
  }

}