using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class AnimLoopRandomStateMachine : StateMachineBehaviour
{
  [Tooltip("How many animations are there in blend tree. (This is clunky)")]
  public int animCount = 1;

  [Tooltip("Blend variable parameter, like in Animator's parameters list")]
  public string blendVariableName = "IdleAnimIdx";

  public bool debugLogChanges = false;


  // OnStateEnter is called before OnStateEnter is called on any state inside this state machine
  // override public void OnStateEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  // {
  // }

  // OnStateUpdate is called before OnStateUpdate is called on any state inside this state machine
  //override public void OnStateUpdate(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  //{
  //}

  // OnStateExit is called before OnStateExit is called on any state inside this state machine
  // override public void OnStateExit(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  // {
  // }

  // OnStateMove is called before OnStateMove is called on any state inside this state machine
  //override public void OnStateMove(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  //{
  //}

  // OnStateIK is called before OnStateIK is called on any state inside this state machine
  //override public void OnStateIK(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
  //{
  //}

  // OnStateMachineEnter is called when entering a state machine via its Entry Node
  override public void OnStateMachineEnter(Animator animator, int stateMachinePathHash)
  {
    // Debug.Log($"OnStateMachineEnter: {blendVariableName}");
    PlayNextRandomAnim(animator);
  }

  // OnStateMachineExit is called when exiting a state machine via its Exit Node
  // override public void OnStateMachineExit(Animator animator, int stateMachinePathHash)
  // {
  // Debug.Log("OnStateMachineExit");
  // PlayNextRandomAnim(animator);
  // }


  private void PlayNextRandomAnim(Animator animator)
  {
    int currAnim = Random.Range(0, animCount);
    // int currAnim = 1; // mock. 1 is the 'swaying' one, that had eyes problem
    if (debugLogChanges)
    {
      Debug.Log($"Anim {blendVariableName}: {currAnim}");
    }

    animator.SetInteger(blendVariableName, currAnim);
  }
}
