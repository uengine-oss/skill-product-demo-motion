# Product Demo Motion

A Codex skill for turning screen recordings into short, silent product showcase videos with smooth perspective camera motion and animated Korean feature captions.

## Visual style

- Elegant Korean serif and classic English serif typography
- Clean white and light gray background
- Animated noun-style feature titles and sequential supporting keywords
- Perspective camera movement with smooth acceleration and deceleration
- 1080p, 60 fps, no audio track
- No progress bars, decorative sliders, or persistent footer branding

The renderer runs locally with Python, Pillow, and FFmpeg. It uses 2.5D perspective transformations of flat recordings, rather than a full 3D scene.

## Install

Clone this repository into your Codex skills directory:

```sh
git clone https://github.com/uengine-oss/skill-product-demo-motion.git ~/.codex/skills/product-demo-motion
```

If the destination already exists, update the existing installation instead of cloning over it.

## Use

Ask Codex:

> Use $product-demo-motion to create a short feature showcase from these screen recordings.

Or in Korean:

> $product-demo-motion으로 이 화면 녹화에서 핵심 기능을 골라 밝은 톤의 짧은 제품 소개 영상을 만들어줘.

See [SKILL.md](SKILL.md) for the workflow and [references/config.md](references/config.md) for the rendering configuration and command-line usage.

## Requirements

- Python 3 and Pillow
- FFmpeg and ffprobe with zoompan, perspective, rotate, and xfade filters
- Installed Korean and English serif fonts; font paths can be configured

Fonts and source recordings are not bundled.

## Files

- `SKILL.md`: Skill instructions
- `agents/openai.yaml`: Codex discovery metadata
- `scripts/render.py`: Config-driven local video renderer
- `references/config.md`: Configuration reference
