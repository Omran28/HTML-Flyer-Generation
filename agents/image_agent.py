import torch
from diffusers import DiffusionPipeline
from typing import List

# Load Stable Diffusion once globally (for efficiency)
pipe = DiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    use_safetensors=True,
).to("cuda")

pipe.enable_xformers_memory_efficient_attention()

# ---------------------------------------------------------
# Node Definition
# ---------------------------------------------------------
def image_generator_node(state: "FlyerState") -> "FlyerState":
    """
    Generates flyer sticker images using Stable Diffusion.
    Prompts and number of images are extracted from the previous node's state.
    """

    try:
        theme = state.get("flyer_theme", "technology flyer")
        num_stickers = state.get("num_stickers", 4)
        concepts: List[str] = state.get(
            "sticker_concepts",
            ["AI", "robot hand", "futuristic laptop", "neon globe"],
        )

        # Log
        state.log(f"🎨 [image_generator_node] Generating {num_stickers} images for theme: '{theme}'")

        generated_images = []

        for i in range(num_stickers):
            # Compose a natural prompt
            concept = concepts[i % len(concepts)]
            prompt = f"{concept} design for a {theme} flyer, futuristic, clean lighting, professional aesthetic"
            state.log(f"🖼️ Generating image {i+1}/{num_stickers}: '{prompt}'")

            img = pipe(
                prompt,
                num_inference_steps=30,
                guidance_scale=7.5,
            ).images[0]

            file_path = f"flyer_part_{i}.png"
            img.save(file_path)
            generated_images.append(file_path)

            state.log(f"✅ Saved {file_path}")
            torch.cuda.empty_cache()  # clear VRAM

        # Update state
        state["generated_images"] = generated_images
        state.log("🚀 [image_generator_node] Image generation completed successfully.")

    except Exception as e:
        state.log(f"❌ [image_generator_node] Error: {str(e)}")

    return state
