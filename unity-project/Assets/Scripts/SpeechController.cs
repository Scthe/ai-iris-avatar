using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;


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

  // [Tooltip("Start audio first. After delay start lipsync animation. Usually not recommended.")]
  // public bool playSoundBeforeLipSync = false;

  void Start()
  {
    // TODO reset clip etc. on the lipsync object
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
      Speak(initialAudioClip);
    }
  }

  public void Speak(AudioClip audioClip)
  {
    PlayLipSyncAnimation(audioClip);
    PlaySpeechSound(audioClip);

    // copy members just in case
    // StartCoroutine(SpeakCoroutine(audioClip, audioDelay, playSoundBeforeLipSync));
  }

  /*
    private IEnumerator SpeakCoroutine(AudioClip audioClip, int audioDelay, bool playSoundBeforeLipSync)
    {
      Func<bool, bool> playSoundOrAnimation = (isPlaySound) => isPlaySound ? PlaySpeechSound(audioClip) : PlayLipSyncAnimation(audioClip);
      Debug.Log("dt:" + MyUtils.s2ms(Time.deltaTime) + "ms");

      playSoundOrAnimation(playSoundBeforeLipSync);

      if (audioDelay > 0)
      {
        yield return MyUtils.wait(MyUtils.ms2s((float)audioDelay));
      }

      Debug.Log("dt:" + MyUtils.s2ms(Time.deltaTime) + "ms");
      playSoundOrAnimation(!playSoundBeforeLipSync);
    }
  */

  public void SpeakWavFileFromBytes(byte[] bytes)
  {
    var pcmData = PcmData.FromBytes(bytes);
    var audioClip = AudioClip.Create("pcm", pcmData.Length, pcmData.Channels, pcmData.SampleRate, false);
    audioClip.SetData(pcmData.Value, 0);

    Speak(audioClip);
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
}
