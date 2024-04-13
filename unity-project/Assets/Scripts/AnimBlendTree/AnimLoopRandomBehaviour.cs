using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/*
 * Unused, just for my own tests.
 * 
 * @see AnimLoopRandomStateMachine instead
 */

public class AnimIdleBehaviour : StateMachineBehaviour
{
  [Tooltip("?Time when 2 animations will be blended between?")]
  public float dampTime = 0.2f;

  [Tooltip("How many animations are there in blend tree. (This is clunky)")]
  public int animCount = 1;

  [Tooltip("Blend variable parameter, like in Animator's parameters list")]
  public string blendVariableName = "IdleAnimIdx";

  public bool debugLogChanges = false;

  private static readonly int ANIM_NONE = -2;

  private int currAnim = ANIM_NONE;
  private bool isTranstioningToNextAnim = false;

  // OnStateEnter is called when a transition starts and the state machine starts to evaluate this state
  override public void OnStateEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  {
    currAnim = ANIM_NONE;
    isTranstioningToNextAnim = false;
  }

  // OnStateUpdate is called on each Update frame between OnStateEnter and OnStateExit callbacks
  override public void OnStateUpdate(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  {
    bool willSoonEnd = (stateInfo.normalizedTime % 1) > 0.98;
    bool hasStartedNextAnim = (stateInfo.normalizedTime % 1) > 0.02;
    bool needsNextAnim = currAnim == ANIM_NONE || willSoonEnd;

    if (hasStartedNextAnim && isTranstioningToNextAnim && !willSoonEnd)
    {
      // has to be first.
      // make sure this prop can be changed if we call PlayNextRandomAnim
      // Debug.Log($"Next anim has started, isTranstioningToNextAnim<-false");
      isTranstioningToNextAnim = false;
    }

    if (needsNextAnim && !isTranstioningToNextAnim)
    {
      isTranstioningToNextAnim = true;
      PlayNextRandomAnim(animator);
    }
  }

  private void PlayNextRandomAnim(Animator animator)
  {
    var nextAnim = Random.Range(0, animCount);
    if (debugLogChanges)
    {
      Debug.Log($"Anim {blendVariableName}: {currAnim} -> {nextAnim}");
    }

    if (currAnim != nextAnim)
    {
      currAnim = nextAnim;
      SetIdleAnimIdx(animator, currAnim);
    }
  }

  private void SetIdleAnimIdx(Animator animator, int idx)
  {
    //TODO goes through intermediate states e.g. 1->5 becomes: 1->2->3->4->5
    // animator.SetFloat(blendVariableName, idx, dampTime, Time.deltaTime);
    animator.SetFloat(blendVariableName, (float)idx);
  }

  // OnStateExit is called when a transition ends and the state machine finishes evaluating this state
  //override public void OnStateExit(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  //{
  //    
  //}

  // OnStateMove is called right after Animator.OnAnimatorMove()
  //override public void OnStateMove(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  //{
  //    // Implement code that processes and affects root motion
  //}

  // OnStateIK is called right after Animator.OnAnimatorIK()
  //override public void OnStateIK(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  //{
  //    // Implement code that sets up animation IK (inverse kinematics)
  //}
}
