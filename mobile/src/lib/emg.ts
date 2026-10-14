/**
 * EMG signal utilities for the mobile client.
 *
 * generateDemoWindow() produces a synthetic EMG-like signal that can be
 * submitted to the backend for end-to-end testing when no real hardware
 * or dataset sample is available. It is clearly labelled as synthetic
 * throughout the UI — it must never be presented as real data.
 */

const N_CHANNELS = 10;
const N_SAMPLES = 200; // 200 samples @ 2 kHz ≈ 100 ms window

/**
 * Generate a synthetic EMG window with noise + simulated burst activity.
 * Shape returned: [n_channels][n_samples] (matches PredictRequest.raw_emg).
 */
export function generateDemoWindow(gestureHint?: string): number[][] {
  const channels: number[][] = [];

  for (let ch = 0; ch < N_CHANNELS; ch++) {
    const samples: number[] = [];
    // Baseline noise
    for (let t = 0; t < N_SAMPLES; t++) {
      const noise = (Math.random() - 0.5) * 0.05;
      // Simulate a burst in the middle of the window for some channels
      const burst =
        t > 60 && t < 140 && ch < 5
          ? Math.sin((t - 60) * 0.2) * (0.3 + Math.random() * 0.2)
          : 0;
      samples.push(noise + burst);
    }
    channels.push(samples);
  }

  return channels;
}

/** Format confidence as a percentage string, or 'N/A' when absent. */
export function formatConfidence(confidence: number | null): string {
  if (confidence === null) return 'N/A';
  return `${(confidence * 100).toFixed(1)}%`;
}

/** Compute per-channel RMS for a [channels][samples] array. */
export function channelRms(emg: number[][]): number[] {
  return emg.map((ch) => {
    const sumSq = ch.reduce((acc, v) => acc + v * v, 0);
    return Math.sqrt(sumSq / ch.length);
  });
}
