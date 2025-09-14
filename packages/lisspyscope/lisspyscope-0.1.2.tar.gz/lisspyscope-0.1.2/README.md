# `lisspyscope`

_A compact Python library for synthesising, visualising and analysing Lissajous figures._

***

## Overview

`lisspyscope` produces **phase–accurate, gap-free stereo signals** whose x-y trace on an oscilloscope forms a mathematically closed Lissajous curve.

It was developed to support undergraduate laboratories on coupled oscillations and phase relationships. The library provides reproducible, phase-accurate audio–visual stimuli that align with learning objectives in introductory and intermediate physics courses.


***

## Installation

```bash
# audio only
pip install lisspyscope

# audio + plotting support
pip install lisspyscope[plot]
```

All wheels are pure-Python; no compilation step is required.

***

## Core Features

- **Auto-closing buffers**
The generator computes the least-common-multiple of channel periods so every trace starts and ends at identical phase.
- **Exact single-buffer looping**
Continuous playback uses the same closed buffer, ensuring no clicks, drifts or cumulative phase error.
- **Lightweight dependency stack**
- **Deterministic output** – Given identical parameters and NumPy version, the generated buffer is bit-for-bit reproducible.
***

## API Summary

| Function | Purpose | Key Parameters |
| :-- | :-- | :-- |
| `generate_lissajous()` | Return `(buffer, sr)`—float32 stereo NumPy array. | `base_freq`, `l_fact`, `r_fact`, `phase_deg`, `sr` |
| `play_lissajous()` | Loop the buffer indefinitely (blocking). | as above |
| `plot_lissajous()` | Render the trace with Matplotlib. | as above |

### Parameter Reference

| Name | Type | Default | Meaning |
| :-- | :-- | :-- | :-- |
| `base_freq` | float | 1,000 Hz | Base frequency |
| `l_fact` | int | 1 | Left/X multiplier f_x = `l_fact` . `base_freq` |
| `r_fact` | int | 1 | Right/Y multiplier f_y = `r_fact` . `base_freq` |
| `phase_deg` | float | 90° | Phase offset of f_y. |
| `sr` | int | 48,000 | Sample rate (samples s⁻¹). |


***

## Minimal Working Examples

```python
import lisspyscope as ls
```

```python
# 1. Classic circle (1 : 1, 90°)
ls.plot_lissajous()        # non-blocking figure
ls.play_lissajous()        # endless tone, Ctrl-C to stop

```

```python
# 2. Generate waves with 1 : 3 frequency ratio with 45° phase
ls.plot_lissajous(base_freq=500, l_fact=1, r_fact=3, phase_deg=45)

```

```python
# 3. Retrieve closed buffer for custom analysis
buf, sr = ls.generate_lissajous(base_freq=250, l_fact=1, r_fact=4, phase_deg=0)
# buf.shape → (192, 2) for 250 Hz at 48 kHz
```
***

## License

MIT—you are free to use, modify and distribute, provided the copyright notice is retained.

