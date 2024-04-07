using System;
using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// Based on code by https://stackoverflow.com/users/1934546/fibrizo-raziel
// https://stackoverflow.com/questions/16078254/create-audioclip-from-byte
// https://stackoverflow.com/questions/35228767/noisy-audio-clip-after-decoding-from-base64/68965193#68965193
// https://creativecommons.org/licenses/by-sa/4.0/

public readonly struct PcmHeader
{
  #region Public types & data

  public int BitDepth { get; }
  public int AudioSampleSize { get; }
  public int AudioSampleCount { get; }
  public ushort Channels { get; }
  public int SampleRate { get; }
  public int AudioStartIndex { get; }
  public int ByteRate { get; }
  public ushort BlockAlign { get; }

  #endregion

  #region Constructors & Finalizer

  private PcmHeader(int bitDepth,
      int audioSize,
      int audioStartIndex,
      ushort channels,
      int sampleRate,
      int byteRate,
      ushort blockAlign)
  {
    BitDepth = bitDepth;
    _negativeDepth = Mathf.Pow(2f, BitDepth - 1f);
    _positiveDepth = _negativeDepth - 1f;

    AudioSampleSize = bitDepth / 8;
    AudioSampleCount = Mathf.FloorToInt(audioSize / (float)AudioSampleSize);
    AudioStartIndex = audioStartIndex;

    Channels = channels;
    SampleRate = sampleRate;
    ByteRate = byteRate;
    BlockAlign = blockAlign;
  }

  #endregion

  #region Public Methods

  public static PcmHeader FromBytes(byte[] pcmBytes)
  {
    using var memoryStream = new MemoryStream(pcmBytes);
    return FromStream(memoryStream);
  }

  public static PcmHeader FromStream(Stream pcmStream)
  {
    pcmStream.Position = SizeIndex;
    using BinaryReader reader = new BinaryReader(pcmStream);

    int headerSize = reader.ReadInt32();  // 16
    ushort audioFormatCode = reader.ReadUInt16(); // 20

    string audioFormat = GetAudioFormatFromCode(audioFormatCode);
    if (audioFormatCode != 1 && audioFormatCode == 65534)
    {
      // Only uncompressed PCM wav files are supported.
      throw new ArgumentOutOfRangeException(nameof(pcmStream),
                                            $"Detected format code '{audioFormatCode}' {audioFormat}, but only PCM and WaveFormatExtensible uncompressed formats are currently supported.");
    }

    ushort channelCount = reader.ReadUInt16(); // 22
    int sampleRate = reader.ReadInt32();  // 24
    int byteRate = reader.ReadInt32();  // 28
    ushort blockAlign = reader.ReadUInt16(); // 32
    ushort bitDepth = reader.ReadUInt16(); //34

    pcmStream.Position = SizeIndex + headerSize + 2 * sizeof(int); // Header end index
    int audioSize = reader.ReadInt32();                            // Audio size index

    return new PcmHeader(bitDepth, audioSize, (int)pcmStream.Position, channelCount, sampleRate, byteRate, blockAlign); // audio start index
  }

  public float NormalizeSample(float rawSample)
  {
    float sampleDepth = rawSample < 0 ? _negativeDepth : _positiveDepth;
    return rawSample / sampleDepth;
  }

  #endregion

  #region Private Methods

  public static string GetAudioFormatFromCode(ushort code)
  {
    switch (code)
    {
      case 1: return "PCM";
      case 2: return "ADPCM";
      case 3: return "IEEE";
      case 7: return "?-law";
      case 65534: return "WaveFormatExtensible";
      default: throw new ArgumentOutOfRangeException(nameof(code), code, "Unknown wav code format.");
    }
  }

  #endregion

  #region Private types & Data

  private const int SizeIndex = 16;

  private readonly float _positiveDepth;
  private readonly float _negativeDepth;

  #endregion
}

public readonly struct PcmData
{
  #region Public types & data

  public float[] Value { get; }
  public int Length { get; }
  public int Channels { get; }
  public int SampleRate { get; }

  #endregion

  #region Constructors & Finalizer

  private PcmData(float[] value, int channels, int sampleRate)
  {
    Value = value;
    Length = value.Length;
    Channels = channels;
    SampleRate = sampleRate;
  }

  #endregion

  #region Public Methods

  public static PcmData FromBytes(byte[] bytes)
  {
    if (bytes == null)
    {
      throw new ArgumentNullException(nameof(bytes));
    }

    PcmHeader pcmHeader = PcmHeader.FromBytes(bytes);
    if (pcmHeader.BitDepth != 16 && pcmHeader.BitDepth != 32 && pcmHeader.BitDepth != 8)
    {
      throw new ArgumentOutOfRangeException(nameof(pcmHeader.BitDepth), pcmHeader.BitDepth, "Supported values are: 8, 16, 32");
    }

    float[] samples = new float[pcmHeader.AudioSampleCount];
    for (int i = 0; i < samples.Length; ++i)
    {
      int byteIndex = pcmHeader.AudioStartIndex + i * pcmHeader.AudioSampleSize;
      float rawSample;
      switch (pcmHeader.BitDepth)
      {
        case 8:
          rawSample = bytes[byteIndex];
          break;

        case 16:
          rawSample = BitConverter.ToInt16(bytes, byteIndex);
          break;

        case 32:
          rawSample = BitConverter.ToInt32(bytes, byteIndex);
          break;

        default: throw new ArgumentOutOfRangeException(nameof(pcmHeader.BitDepth), pcmHeader.BitDepth, "Supported values are: 8, 16, 32");
      }

      samples[i] = pcmHeader.NormalizeSample(rawSample); // normalize sample between [-1f, 1f]
    }

    return new PcmData(samples, pcmHeader.Channels, pcmHeader.SampleRate);
  }

  #endregion
}