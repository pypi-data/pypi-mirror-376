# Image Description Tool
Repository: https://github.com/chazzofalf/image_analysis_and_sd

This tool leverages Ollama models to describe images and generate stable diffusion parameters for recreation in InvokeAI.

## Functionality

- **Image Description:** Uses multiple Ollama models (gemma3:27b, llava:latest, llama4:scout, mistral-small3.2:24b, Moondream:latest, llama3.2-vision:latest) to generate descriptions of an input image.
- **Summarization:** Combines the individual descriptions into a single, comprehensive summary using `gpt-oss:120b`.
- **Stable Diffusion Parameter Generation:** Extracts parameters (positive prompt, negative prompt, step count, CFG scale, image dimensions, and suggested model/scheduler) suitable for recreating the image in InvokeAI, using `gpt-oss:120b`.

## Usage

1.  Ensure you have Ollama installed and configured.
2.  Run the `image_describer.py` script with the following arguments:

    ```bash
    python image_describer.py <image_path> <output_file>
    ```

    *   `<image_path>`: Path to the input image.
    *   `<output_file>`: Path to the output file (summary will be written to this file, and stable diffusion parameters will be written to `<output_file>.sd.txt`).

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/chazzofalf/image_analysis_and_sd
    cd image_analysis_and_sd
    ```
2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    ```
3.  Activate the virtual environment:
    *   **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Example

Here's an example using the `Scout.jpg` image:

*   **Image:** `Scout.jpg`
*   **Description:** `Scout.jpg.txt`
*   **Stable Diffusion Instructions:** `Scout.jpg.txt.sd.txt`

## Quick-Start “InvokeAI” Settings

| Item | Recommendation |
|------|-----------------|
| **Positive Prompt** | `a small dark-fur animal curled up sleeping on a cozy patterned blanket, realistic photography, soft natural light filtered through a sheer white curtain, navy-blue blanket with tiny white/ light-blue four-petal flower motif, lightly rumpled sky-blue sheet underneath, plain white wall background, subtle window with diffused daylight, shallow depth of field, ultra-sharp focus on animal’s face, warm-amber glow, highly detailed fur, plush texture, intimate bedroom scene, 8k resolution, cinematic composition, top-down angle` |
| **Negative Prompt** | `low-resolution, blurry, jpeg artifacts, over-exposed, under-exposed, color banding, chromatic aberration, watermark, text, signature, frame, lens flare, cartoon, illustration, anime, painting, oil-painting, stylized, vignette, grainy, noise, over-sharpened, HDR, unrealistic shadows, missing limbs, extra paws, duplicated body parts, deformed anatomy, unrealistic proportions, plastic look` |
| **Steps** | **35–45** (35 works well for most cases; push to 45 if you need extra fine detail on fur and fabric) |
| **CFG Scale** | **7.5–9** (7.5 for a balanced blend of prompt fidelity and creativity; 9 if you want the image to follow the prompt almost verbatim) |
| **Suggested Image Dimensions** | **768 × 1024** (portrait – good for a bedside view) or **1024 × 1280** if you want a bit more vertical space for the window and wall. |
| **Best Stable-Diffusion Model** | **Stable Diffusion XL 1.0 (or XL 1.0‑refiner)** – it handles realistic lighting, fine fur texture and fabric patterns far better than the 1.5 checkpoint. If you have limited VRAM, the **SDXL‑Turbo** checkpoint can also produce good results at a lower cost, but expect slightly less micro‑detail. |
| **Best Scheduler** | **DPM++ 2M Karras** (very stable for photorealistic output) – alternatively **Euler‑a** works well for a smoother, less “noisy” finish. |

### How the Prompt Was Built (Why It Works)

- **Subject Detail** – “small dark‑fur animal” covers both the dog‑or‑cat ambiguity while keeping the description concise for the model. Adding “curled up sleeping” forces the pose.
- **Fabric & Pattern** – Explicitly naming the **navy‑blue blanket** and **tiny white/light‑blue four‑petal flower motif** gives the model a concrete visual cue for the patterned textile, which is often a weak point for generic prompts.
- **Lighting & Atmosphere** – Phrases like “soft natural light filtered through a sheer white curtain”, “warm‑amber glow”, and “diffused daylight” steer the model toward the low‑key, gently illuminated mood described.
- **Depth & Focus** – “shallow depth of field”, “ultra‑sharp focus on animal’s face”, and “top‑down angle” ensure the animal is the clear focal point while the background stays softly rendered.
- **Quality Tags** – “realistic photography”, “8k resolution”, “cinematic composition” push the model toward a high‑detail, photorealistic output rather than an illustration or stylized rendering.

### Quick “Copy‑Paste” Block for InvokeAI

```yaml
prompt: |
  a small dark-fur animal curled up sleeping on a cozy patterned blanket, realistic photography, soft natural light filtered through a sheer white curtain, navy-blue blanket with tiny white light-blue four-petal flower motif, lightly rumpled sky-blue sheet underneath, plain white wall background, subtle window with diffused daylight, shallow depth of field, ultra-sharp focus on animal’s face, warm-amber glow, highly detailed fur, plush texture, intimate bedroom scene, 8k resolution, cinematic composition, top-down angle
negative_prompt: |
  low-resolution, blurry, jpeg artifacts, over-exposed, under-exposed, color banding, chromatic aberration, watermark, text, signature, frame, lens flare, cartoon, illustration, anime, painting, oil-painting, stylized, vignette, grainy, noise, over-sharpened, HDR, unrealistic shadows, missing limbs, extra paws, duplicated body parts, deformed anatomy, unrealistic proportions, plastic look
steps: 40
cfg_scale: 8
width: 768
height: 1024
sampler: DPM++ 2M Karras
model: stabilityai/stable-diffusion-xl-base-1.0   # or the XL‑Turbo checkpoint if VRAM is limited
```

Feel free to tweak the **CFG** (higher for stricter adherence) or **steps** (more steps for extra fine fur detail). Adjust the **width/height** if you prefer a wider composition that includes more of the window or wall.  

Happy generating! 🎨🖼️

## Dependencies

-   Ollama
-   Python 3.10.18

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

<small>Made with <a href="https://cline.bot">Cline</a> and <a href="https://ollama.com">Ollama</a>, using models <a href="https://ollama.com/library/gpt-oss:120b">gpt-oss:120b</a> and <a href="https://ollama.com/library/gemma3:27b">gemma3:27b</a>.</small>
