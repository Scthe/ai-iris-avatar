//
//SpingManager.cs for unity-chan!
//
//Original Script is here:
//ricopin / SpingManager.cs
//Rocket Jump : http://rocketjump.skr.jp/unity3d/109/
//https://twitter.com/ricopin416
//
//Revised by N.Kobayashi 2014/06/24
//           Y.Ebata
//
using UnityEngine;
using System.Collections;

namespace UnityChan
{
  public class SpringManager : MonoBehaviour
  {
    //Kobayashi
    // DynamicRatio is paramater for activated level of dynamic animation 
    [Tooltip("Only animates spring bones, that have threshold lower than this")]
    [Range(0.0f, 1.0f)]
    public float dynamicRatio = 1.0f;

    [Header("Forces")]
    //Ebata
    [Tooltip("Stiffness: additional force along the boneAxis. 1.0 prohibits movement. 0.0 more movement")]
    public float stiffnessForce = 0.002f;
    [Tooltip("Stiffness multiplier for each child spring bone. Usually set it to const 1.0")]
    public AnimationCurve stiffnessCurve = AnimationCurve.Constant(0.0f, 1.0f, 1.0f);
    [Tooltip("Drag: limit displacement between consequtive frames (prevTipPos - currTipPos). 1.0 slows movement. 0.0 more movement")]
    public float dragForce = 0.001f;
    [Tooltip("Drag multiplier for each child spring bone. Usually set it to const 1.0")]
    public AnimationCurve dragCurve = AnimationCurve.Constant(0.0f, 1.0f, 1.0f);


    [Header("Child springs")]
    public SpringBone[] springBones;

    void Start()
    {
      UpdateParameters();
    }

#if UNITY_EDITOR
		void Update ()
		{

		//Kobayashi
		if(dynamicRatio >= 1.0f)
			dynamicRatio = 1.0f;
		else if(dynamicRatio <= 0.0f)
			dynamicRatio = 0.0f;
		//Ebata
		UpdateParameters();

		}
#endif
    private void LateUpdate()
    {
      //Kobayashi
      if (dynamicRatio != 0.0f)
      {
        for (int i = 0; i < springBones.Length; i++)
        {
          if (dynamicRatio > springBones[i].threshold)
          {
            springBones[i].UpdateSpring();
          }
        }
      }
    }

    private void UpdateParameters()
    {
      UpdateParameter("stiffnessForce", stiffnessForce, stiffnessCurve);
      UpdateParameter("dragForce", dragForce, dragCurve);
    }

    private void UpdateParameter(string fieldName, float baseValue, AnimationCurve curve)
    {
#if UNITY_EDITOR
			var start = curve.keys [0].time;
			var end = curve.keys [curve.length - 1].time;
			//var step	= (end - start) / (springBones.Length - 1);
		
			var prop = springBones [0].GetType ().GetField (fieldName, System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public);
		
			for (int i = 0; i < springBones.Length; i++) {
				//Kobayashi
				if (!springBones [i].isUseEachBoneForceSettings) {
          // Custom fix: originally, this had no ternary operator. It divided by 0 and failed.
					var scale = springBones.Length > 1 ? curve.Evaluate (start + (end - start) * i / (springBones.Length - 1)) : 1;
					prop.SetValue (springBones [i], baseValue * scale);
				}
			}
#endif
    }
  }
}