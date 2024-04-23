using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.Events;

using static MyUtils;

[RequireComponent(typeof(AudioSource))]
public class SpeechController : MonoBehaviour
{
  [Tooltip("Initial clip to play")]
  public AudioClip initialAudioClip = null;

  [Tooltip("Mute initial clip")]
  public bool muteInitial = false;


  public bool loop = false;

  [Tooltip("GameObject that contains Lipsync components")]
  public AudioSource speakerWithLipSync;

  [Header("Timings")]
  [Tooltip("Induce audio delay when compared to lipsync animation. In miliseconds.")]
  [Range(0, 1000)]
  public int audioDelay = 0;


  [Tooltip("Handlers for speaking start/stop.")]
  public UnityEvent<bool> onIsSpeakingChange;

  // [Tooltip("Start audio first. After delay start lipsync animation. Usually not recommended.")]
  // public bool playSoundBeforeLipSync = false;

  private Queue<AudioClip> clipQueue = new Queue<AudioClip>();

  // Breath is an idle animation of mouth. I.E. when not speaking

  [Header("Breathing")]
  [Tooltip("Shortest possible time between breaths (in seconds).")]
  [Range(0.1f, 10.0f)]
  public float BreathingIntervalMin = 3.0f;

  [Tooltip("Longest possible time between breaths (in seconds).")]
  [Range(0.1f, 10.0f)]
  public float BreathingIntervalMax = 5.0f;

  [Tooltip("Duration of the inhale (in seconds).")]
  [Range(0.1f, 5.0f)]
  public float InhaleDuration = 3.0f;

  [Tooltip("Inhale shape key strength")]
  [Range(0.0f, 1.0f)]
  public float InhaleStrength = 0.3f;

  [Tooltip("Pause between inhale and exhale (in seconds).")]
  [Range(0.1f, 5.0f)]
  public float BreathHoldDuration = 0.5f;

  [Tooltip("Duration of the exnhale (in seconds).")]
  [Range(0.1f, 5.0f)]
  public float ExhaleDuration = 2.0f;

  [Tooltip("Exhale shape key strength: mouth")]
  [Range(0.0f, 1.0f)]
  public float ExhaleStrength = 0.03f;

  [Tooltip("Exhale shape key strength: jaw")]
  [Range(0.0f, 1.0f)]
  public float ExhaleJawStrength = 0.08f; // Suprisingly a lot of jaw movement TBH

  public AnimationCurve breathingInterpolationCurve = AnimationCurve.EaseInOut(0f, 0f, 0f, 0f);


  private string SK_BREATH_EXHALE_L = "MOUTH-btm_lip_out.L";
  private string SK_BREATH_EXHALE_R = "MOUTH-btm_lip_out.R";
  private string SK_BREATH_INHALE_R = "NASAL-flare.R";
  private string SK_BREATH_INHALE_L = "NASAL-flare.L";
  private string SK_BREATH_INHALE2_R = "NASAL-sneer.R";
  private string SK_BREATH_INHALE2_L = "NASAL-sneer.L";
  private string SK_BREATH_JAW = "jaw-down";
  private IEnumerator breathingCoroutine;
  private bool prevIsSpeaking = false;



  void Start()
  {
    speakerWithLipSync.mute = true;
    speakerWithLipSync.playOnAwake = false;
    speakerWithLipSync.loop = loop;
    speakerWithLipSync.GetComponent<OVRLipSyncContext>().audioLoopback = false; // disable sound emitting

    var myAudioSource = GetComponent<AudioSource>();
    if (myAudioSource)
    {
      myAudioSource.loop = loop;
    }

    if (!muteInitial)
    {
      ScheduleNextAudioClip(initialAudioClip);
    }
  }

  void Update()
  {
    var isSpeaking = IsSpeaking();

    if (!isSpeaking)
    {
      if (clipQueue.Count > 0)
      {
        StopBreathing();
        PlayNextAudioClip();
        isSpeaking = true;
      }
      else
      {
        EnsureBreathing(); // nice name btw.
      }
    }

    if (prevIsSpeaking != isSpeaking)
    {
      onIsSpeakingChange?.Invoke(isSpeaking);
    }
    prevIsSpeaking = isSpeaking;
  }

  public void PlayNextAudioClip()
  {
    var audioClip = clipQueue.Dequeue();

    // Alternative is to use .playscheduled(), but we want to always
    // start both clips at same time.
    // https://johnleonardfrench.com/ultimate-guide-to-playscheduled-in-unity/
    PlayLipSyncAnimation(audioClip);
    PlaySpeechSound(audioClip);
  }

  private bool IsSpeaking()
  {
    return speakerWithLipSync.isPlaying || GetComponent<AudioSource>().isPlaying;
  }

  public void SpeakWavFileFromBytes(byte[] bytes)
  {
    var pcmData = PcmData.FromBytes(bytes);
    var audioClip = AudioClip.Create("pcm", pcmData.Length, pcmData.Channels, pcmData.SampleRate, false);
    audioClip.SetData(pcmData.Value, 0);

    ScheduleNextAudioClip(audioClip);
  }

  private void ScheduleNextAudioClip(AudioClip audioClip)
  {
    if (audioClip != null)
    {
      clipQueue.Enqueue(audioClip);
    }
  }

  private bool PlaySpeechSound(AudioClip audioClip)
  {
    var myAudioSource = GetComponent<AudioSource>();
    if (myAudioSource)
    {
      myAudioSource.clip = audioClip;
      if (audioDelay > 0)
      {
        var nextEventTime = AudioSettings.dspTime + MyUtils.ms2s((float)audioDelay);
        myAudioSource.PlayScheduled(nextEventTime);
      }
      else
      {
        myAudioSource.Play();
      }
    }
    return true;
  }

  private bool PlayLipSyncAnimation(AudioClip audioClip)
  {
    if (speakerWithLipSync)
    {
      speakerWithLipSync.mute = false;
      speakerWithLipSync.clip = audioClip;
      speakerWithLipSync.Play();
    }
    return true;
  }

  ///////// Breathing
  private void EnsureBreathing()
  {
    if (breathingCoroutine == null)
    {
      breathingCoroutine = BreathingCourotine();
      StartCoroutine(breathingCoroutine);
    }
  }

  ///  Nice name btw.
  private void StopBreathing()
  {
    if (breathingCoroutine != null)
    {
      StopCoroutine(breathingCoroutine);
      breathingCoroutine = null;
      ClearBreathShapeKeys();
    }
  }

  public IEnumerator BreathingCourotine()
  {
    while (true)
    {
      var interval = UnityEngine.Random.Range(BreathingIntervalMin, BreathingIntervalMax);
      yield return MyUtils.wait(interval);

      // inhale: nose flares
      var keyframes = CalculateBreathingInterpolation(InhaleDuration);
      float dt = InhaleDuration / (float)keyframes.Length;
      foreach (float progress in keyframes)
      {
        ApplyBreathShapeKeys_Nostrils(progress);
        yield return MyUtils.wait(dt);
      }
      ClearBreathShapeKeys();

      yield return MyUtils.wait(BreathHoldDuration);

      // exhale
      keyframes = CalculateBreathingInterpolation(ExhaleDuration);
      dt = ExhaleDuration / (float)keyframes.Length;
      foreach (float progress in keyframes)
      {
        ApplyBreathShapeKeys_Mouth(progress);
        yield return MyUtils.wait(dt);
      }
      ClearBreathShapeKeys();
    }
  }

  private float[] CalculateBreathingInterpolation(float duration)
  {
    int steps = (int)Math.Ceiling(duration / Time.deltaTime) / 2;
    float dt = duration / (float)steps;

    Func<float, float> ff = x => 1.0f - Math.Abs(x * 2f - 1f);
    float[] keyframes = Enumerable.Range(1, steps - 1).Select(
      x => breathingInterpolationCurve.Evaluate(ff(x / (float)steps))
    // x => ff(x / (float)(steps))
    ).ToArray();
    return keyframes;
  }

  private void ApplyBreathShapeKeys_Nostrils(float progress)
  {
    var bodyMesh = speakerWithLipSync.GetComponent<SkinnedMeshRenderer>();
    var str = progress * InhaleStrength;
    SafeSetBlendShapeWeight(bodyMesh, SK_BREATH_INHALE_L, str);
    SafeSetBlendShapeWeight(bodyMesh, SK_BREATH_INHALE_R, str);
    SafeSetBlendShapeWeight(bodyMesh, SK_BREATH_INHALE2_L, str);
    SafeSetBlendShapeWeight(bodyMesh, SK_BREATH_INHALE2_R, str);
  }

  private void ApplyBreathShapeKeys_Mouth(float progress)
  {
    var bodyMesh = speakerWithLipSync.GetComponent<SkinnedMeshRenderer>();
    var str = progress * ExhaleStrength;
    SafeSetBlendShapeWeight(bodyMesh, SK_BREATH_EXHALE_L, str);
    SafeSetBlendShapeWeight(bodyMesh, SK_BREATH_EXHALE_R, str);
    SafeSetBlendShapeWeight(bodyMesh, SK_BREATH_JAW, ExhaleJawStrength * progress);
  }

  private void ClearBreathShapeKeys()
  {
    ApplyBreathShapeKeys_Mouth(0.0f);
    ApplyBreathShapeKeys_Nostrils(0.0f);
  }
}
