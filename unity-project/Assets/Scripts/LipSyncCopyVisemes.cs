using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Linq;

public class LipSyncCopyVisemes : MonoBehaviour
{
  public OVRLipSyncContextBase lipsyncContext = null;
  public SkinnedMeshRenderer skinnedMeshRenderer = null;
  public int[] visemeToBlendTargets = Enumerable.Range(0, OVRLipSync.VisemeCount).ToArray();


  // Start is called before the first frame update
  void Start()
  {
  }

  void Awake()
  {
  }

  void Update()
  {
    if ((lipsyncContext != null) && (skinnedMeshRenderer != null))
    {
      // get the current viseme frame
      OVRLipSync.Frame frame = lipsyncContext.GetCurrentPhonemeFrame();
      if (frame != null)
      {
        SetVisemeToMorphTarget(frame);
      }
    }
  }

  void SetVisemeToMorphTarget(OVRLipSync.Frame frame)
  {
    for (int i = 0; i < visemeToBlendTargets.Length; i++)
    {
      SafeSetBlendShapeWeight(visemeToBlendTargets[i], frame.Visemes[i]);
    }
  }

  void SafeSetBlendShapeWeight(int blendShapeIdx, float value)
  {
    if (value > 0.8)
    {
      // Debug.Log(name + ":" + skinnedMeshRenderer.sharedMesh.GetBlendShapeName(blendShapeIdx));
    }

    if (blendShapeIdx != -1 && blendShapeIdx < skinnedMeshRenderer.sharedMesh.blendShapeCount)
    {
      // Viseme blend weights are in range of 0->1.0, we need to make range 100
      skinnedMeshRenderer.SetBlendShapeWeight(
          blendShapeIdx,
          value * 100.0f);
    }
  }
}
