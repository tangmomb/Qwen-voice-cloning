from __future__ import annotations

import argparse
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


DEFAULT_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
_MODEL_CACHE: dict[tuple[str, str, str, str], Qwen3TTSModel] = {}


def existing_file(value: str, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"{label} introuvable: {path}")
    return path


def resolve_dtype(value: str) -> torch.dtype:
    if value == "float16":
        return torch.float16
    if value == "bfloat16":
        return torch.bfloat16
    return torch.float32


def resolve_device(value: str) -> str:
    if value == "auto":
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    return value


def load_qwen_model(
    *,
    model_name: str = DEFAULT_MODEL,
    device: str = "cpu",
    dtype: str = "float32",
    attention: str = "eager",
) -> Qwen3TTSModel:
    resolved_device = resolve_device(device)
    cache_key = (model_name, resolved_device, dtype, attention)
    if cache_key not in _MODEL_CACHE:
        print(f"Chargement {model_name} sur {resolved_device} en {dtype}...")
        _MODEL_CACHE[cache_key] = Qwen3TTSModel.from_pretrained(
            model_name,
            device_map=resolved_device,
            dtype=resolve_dtype(dtype),
            attn_implementation=attention,
        )
    return _MODEL_CACHE[cache_key]


def generate_voice_clone(
    *,
    ref_audio: str | Path,
    ref_text: str,
    text: str,
    output: str | Path,
    model_name: str = DEFAULT_MODEL,
    language: str = "French",
    device: str = "cpu",
    dtype: str = "float32",
    attention: str = "eager",
    max_new_tokens: int = 1024,
    top_p: float | None = None,
    temperature: float | None = None,
    x_vector_only: bool = False,
) -> Path:
    ref_audio_path = existing_file(str(ref_audio), "Audio de reference")
    if not ref_text.strip():
        raise ValueError("ReferenceText est obligatoire.")
    if not text.strip():
        raise ValueError("Le texte a generer est obligatoire.")

    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model = load_qwen_model(
        model_name=model_name,
        device=device,
        dtype=dtype,
        attention=attention,
    )

    generation_kwargs: dict[str, object] = {"max_new_tokens": max_new_tokens}
    if top_p is not None:
        generation_kwargs["top_p"] = top_p
    if temperature is not None:
        generation_kwargs["temperature"] = temperature

    print("Generation Qwen3-TTS...")
    wavs, sample_rate = model.generate_voice_clone(
        text=text,
        language=language,
        ref_audio=str(ref_audio_path),
        ref_text=ref_text,
        x_vector_only_mode=x_vector_only,
        **generation_kwargs,
    )
    sf.write(output_path, wavs[0], sample_rate)
    print(f"Audio genere: {output_path}")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Voice cloning avec Qwen3-TTS Base.")
    parser.add_argument("--ref-audio", required=True, help="Audio de reference.")
    parser.add_argument("--ref-text", required=True, help="Transcription exacte de la reference.")
    parser.add_argument("--text", default="", help="Texte a generer.")
    parser.add_argument("--text-file", default="", help="Fichier texte UTF-8 a generer.")
    parser.add_argument("--output", default="outputs/qwen/qwen_clone.wav", help="Fichier WAV de sortie.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Modele Qwen3-TTS.")
    parser.add_argument("--language", default="French", help="Langue Qwen, ex: French, English, Auto.")
    parser.add_argument("--device", default="cpu", help="cpu, cuda:0, cuda ou auto.")
    parser.add_argument("--dtype", default="float32", choices=("float32", "float16", "bfloat16"))
    parser.add_argument("--attn", default="eager", choices=("eager", "sdpa", "flash_attention_2"))
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--x-vector-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ref_audio = existing_file(args.ref_audio, "Audio de reference")
    text_file = existing_file(args.text_file, "Fichier texte") if args.text_file else None
    text = text_file.read_text(encoding="utf-8") if text_file else args.text
    if not text.strip():
        raise SystemExit("Donne --text ou --text-file.")

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    generate_voice_clone(
        ref_audio=ref_audio,
        ref_text=args.ref_text,
        text=text,
        output=output,
        model_name=args.model,
        language=args.language,
        device=args.device,
        dtype=args.dtype,
        attention=args.attn,
        max_new_tokens=args.max_new_tokens,
        top_p=args.top_p,
        temperature=args.temperature,
        x_vector_only=args.x_vector_only,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
