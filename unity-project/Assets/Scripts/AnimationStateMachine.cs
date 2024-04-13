using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(Animator))]
public class AnimationStateMachine : MonoBehaviour
{
  private static readonly string ANIM_PARAM_IS_SPEAKING = "IsSpeaking";

  private Animator animator;

  void Start()
  {
    animator = GetComponent<Animator>();
  }

  public void HandleSendQuery(string _prompt)
  {
    // Debug.Log($"HandleSendQuery");

    // start transition to 'speak' animations in preparation
    SetIsSpeakingAnimParam(true);
  }

  public void HandleIsSpeakingChange(bool isSpeaking)
  {
    // Debug.Log($"HandleIsSpeakingChange: {isSpeaking}");
    if (!isSpeaking)
    {
      SetIsSpeakingAnimParam(false);
    }
  }

  private void SetIsSpeakingAnimParam(bool value)
  {
    animator.SetBool(ANIM_PARAM_IS_SPEAKING, value);
  }
}
