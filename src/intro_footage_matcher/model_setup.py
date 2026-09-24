from __future__ import annotations


REQUIRED_MODELS = (
    "openai/clip-vit-base-patch32",
    "sentence-transformers/all-MiniLM-L6-v2",
)


def ensure_required_models() -> None:
    """Fail early with an actionable message when offline weights are absent."""
    try:
        from huggingface_hub import snapshot_download
        for model_id in REQUIRED_MODELS:
            snapshot_download(repo_id=model_id, local_files_only=True)
    except Exception as exc:
        raise RuntimeError(
            "Required local vision/semantic model weights are missing. "
            "Connect once and run ./setup.sh before analyzing footage."
        ) from exc


def download_required_models() -> None:
    from sentence_transformers import SentenceTransformer
    from transformers import CLIPModel, CLIPProcessor

    clip_id, text_id = REQUIRED_MODELS
    CLIPModel.from_pretrained(clip_id)
    CLIPProcessor.from_pretrained(clip_id)
    SentenceTransformer(text_id)


def main() -> None:
    print("Provisioning local CLIP and MiniLM model weights...")
    download_required_models()
    ensure_required_models()
    print("Local model weights are ready.")


if __name__ == "__main__":
    main()
