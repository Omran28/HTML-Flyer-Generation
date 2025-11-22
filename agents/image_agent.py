import re, torch
from diffusers import DiffusionPipeline
from core.state import FlyerState
from utils.helpers import save_image_locally, inject_images_for_preview, get_position_coordinates, save_html

# Assuming pipe is defined globally or within a class/factory
pipe = DiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    use_safetensors=True
)
pipe.to("cuda")


def image_generator_node(state: FlyerState) -> FlyerState:
    try:
        images_meta = state.theme_json.get("images", [])
        generated_images = []

        for idx, img_data in enumerate(images_meta):
            # We now have access to border_radius in images_meta, but we only store core generation data here.
            desc = img_data.get("description", f"Flyer image {idx + 1}")
            pos = img_data.get("position", "center")
            size = img_data.get("size", "40%")
            layer = img_data.get("layer", "foreground")
            state.log(f"🖼️ Generating image {idx + 1}: {desc}")
            try:
                img = pipe(
                    f"{desc}, professional high-end flyer, luxurious texture, {state.theme_json.get('theme', {}).get('tone', 'elegant')}",
                    num_inference_steps=25, guidance_scale=7.5).images[0]
                path = save_image_locally(img, idx)
                generated_images.append({"path": path, "pos": pos, "size": size, "layer": layer})
                state.log(f"✅ Image {idx + 1} saved: {path}")
                if torch.cuda.is_available(): torch.cuda.empty_cache()
            except Exception as e:
                state.log(f"❌ Error generating image {idx + 1}: {e}")

        state.generated_images = generated_images

        # Insert placeholders if missing
        html = state.html_output or ""
        for idx in range(len(generated_images)):
            placeholder = f""
            if placeholder not in html:
                div_match = re.search(r'(<div[^>]*>)', html)
                if div_match:
                    insert_pos = div_match.end()
                    html = html[:insert_pos] + placeholder + html[insert_pos:]
                else:
                    html += placeholder

        state.html_final = html
        preview_html = inject_images_for_preview(state.html_final)

        # 💡 FIX for File Saving (Problem 3): Use content_override
        save_path = save_html(state, filename="flyer_original.html", content_override=preview_html)
        state.log(f"💾 HTML with image placeholders saved to: {save_path}")
    except Exception as e:
        state.log(f"❌ [image_generator_node] Critical error: {e}")

    return state