from __future__ import annotations

import argparse
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


DEFAULT_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"


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

    device = "cuda:0" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device == "auto":
        device = "cpu"

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Chargement {args.model} sur {device} en {args.dtype}...")
    model = Qwen3TTSModel.from_pretrained(
        args.model,
        device_map=device,
        dtype=resolve_dtype(args.dtype),
        attn_implementation=args.attn,
    )

    generation_kwargs: dict[str, object] = {"max_new_tokens": args.max_new_tokens}
    if args.top_p is not None:
        generation_kwargs["top_p"] = args.top_p
    if args.temperature is not None:
        generation_kwargs["temperature"] = args.temperature

    print("Generation Qwen3-TTS...")
    wavs, sample_rate = model.generate_voice_clone(
        text=text,
        language=args.language,
        ref_audio=str(ref_audio),
        ref_text=args.ref_text,
        x_vector_only_mode=args.x_vector_only,
        **generation_kwargs,
    )
    sf.write(output, wavs[0], sample_rate)
    print(f"Audio genere: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
