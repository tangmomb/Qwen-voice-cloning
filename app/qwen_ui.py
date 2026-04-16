from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import traceback
import gc
import time
from datetime import datetime
from pathlib import Path

import gradio as gr
import soundfile as sf
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qwen_clone import DEFAULT_MODEL, generate_voice_clone


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_NAME = f"Clone Voice - {DEFAULT_MODEL}"
INPUTS_DIR = PROJECT_ROOT / "inputs"
REFS_DIR = PROJECT_ROOT / "generated_refs"
OUT_DIR = PROJECT_ROOT / "outputs" / "qwen"
LOGS_DIR = PROJECT_ROOT / "logs"
TOOLS_DIR = PROJECT_ROOT / ".tools"
DEFAULT_TEXT = (
    "Bonjour, je m'appelle Claire Martin et je suis professeure de français depuis douze ans. "
    "J'accompagne mes élèves dans la découverte de la littérature, de l'expression écrite et de l'argumentation orale. "
    "Mon objectif est de créer un climat de confiance où chacun peut progresser à son rythme, poser des questions "
    "et développer son esprit critique."
)
BASE_REFERENCE_DURATION_SECONDS = 3.2
WHISPER_MODEL = "large"
ATTENTION = "eager"
MAX_NEW_TOKENS = 768
MAX_RATABLE_OUTPUTS = 24
SUPPORTED_AUDIO_EXTS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac", ".wma"}
STAR_CHOICES = ["1 etoile", "2 etoiles", "3 etoiles", "4 etoiles", "5 etoiles"]
STAR_TO_EXPLORER_RATING = {
    "1 etoile": 1,
    "2 etoiles": 25,
    "3 etoiles": 50,
    "4 etoiles": 75,
    "5 etoiles": 99,
}
STAR_TO_ID3_POPM_RATING = {
    "1 etoile": 1,
    "2 etoiles": 64,
    "3 etoiles": 128,
    "4 etoiles": 196,
    "5 etoiles": 255,
}
WINDOWS_POPM_EMAIL = "Windows Media Player 9 Series"
_FFMPEG_EXE: str | None = None


def _safe_stem(path: str | Path) -> str:
    stem = Path(path).stem
    return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in stem).strip("_") or "voice"


def _run_id(source: Path) -> str:
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_safe_stem(source)}"


def _format_elapsed(seconds: float) -> str:
    seconds = max(0.0, seconds)
    minutes, remaining_seconds = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}min {remaining_seconds:02d}s"
    if minutes:
        return f"{minutes}min {remaining_seconds:02d}s"
    return f"{remaining_seconds}s"


def _run(command: list[str]) -> None:
    try:
        subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    except FileNotFoundError as exc:
        raise gr.Error(
            f"Executable introuvable: {command[0]}\n"
            "Installe les dependances avec .\\scripts\\setup_qwen.ps1, "
            "ou ajoute FFmpeg au PATH Windows."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise gr.Error(f"Commande echouee: {' '.join(command)}\nCode: {exc.returncode}") from exc


def _ffmpeg_exe() -> str:
    global _FFMPEG_EXE
    if _FFMPEG_EXE:
        return _FFMPEG_EXE

    ffmpeg_from_path = shutil.which("ffmpeg")
    if ffmpeg_from_path:
        _FFMPEG_EXE = ffmpeg_from_path
        return _FFMPEG_EXE

    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise gr.Error(
            "FFmpeg est introuvable. Lance .\\scripts\\setup_qwen.ps1 pour installer "
            "imageio-ffmpeg, ou installe FFmpeg et ajoute-le au PATH Windows."
        ) from exc

    imageio_ffmpeg_exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    shim_path = TOOLS_DIR / "ffmpeg.exe"
    if not shim_path.is_file():
        shutil.copy2(imageio_ffmpeg_exe, shim_path)

    _FFMPEG_EXE = str(shim_path)
    ffmpeg_dir = str(shim_path.parent)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    return _FFMPEG_EXE


def _audio_duration(path: str | Path) -> float:
    try:
        info = sf.info(str(path))
    except RuntimeError as exc:
        raise gr.Error(f"Impossible de lire la duree audio: {path}") from exc
    return float(info.frames / info.samplerate)


def _store_upload(uploaded_audio: str) -> Path:
    if not uploaded_audio:
        raise gr.Error("Upload un fichier audio.")

    source = Path(uploaded_audio)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_AUDIO_EXTS:
        suffix = ".wav"

    INPUTS_DIR.mkdir(parents=True, exist_ok=True)
    target = INPUTS_DIR / f"{_safe_stem(source)}{suffix}"
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return target


def _reference_starts(audio_path: Path, count: int, duration: float) -> list[float]:
    total = max(_audio_duration(audio_path), 0.0)
    usable_end = max(total - duration - 0.25, 0.0)
    if count <= 1:
        return [min(20.0, usable_end)]

    first = 0.0 if usable_end < 20 else 20.0
    if usable_end <= first:
        return [first for _ in range(count)]

    step = (usable_end - first) / (count - 1)
    return [round(first + step * index, 2) for index in range(count)]


def _make_reference(source: Path, refs_dir: Path, label: str, start: float, duration: float) -> Path:
    refs_dir.mkdir(parents=True, exist_ok=True)
    start_tag = str(start).replace(",", ".").replace(".", "p")
    duration_tag = str(duration).replace(",", ".").replace(".", "p")
    ref_path = refs_dir / f"{_safe_stem(source)}_{label}_s{start_tag}_d{duration_tag}.wav"

    if not ref_path.is_file():
        _run(
            [
                _ffmpeg_exe(),
                "-y",
                "-ss",
                str(start),
                "-t",
                str(duration),
                "-i",
                str(source),
                "-af",
                "loudnorm,apad=pad_dur=0.2",
                "-ar",
                "24000",
                "-ac",
                "1",
                str(ref_path),
            ]
        )
    return ref_path


def _make_rating_copy(output_path: Path) -> Path:
    mp3_path = output_path.with_suffix(".mp3")
    if mp3_path.is_file():
        return mp3_path

    _run(
        [
            _ffmpeg_exe(),
            "-y",
            "-i",
            str(output_path),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(mp3_path),
        ]
    )
    return mp3_path


def _transcribe_reference(ref_path: Path, refs_dir: Path) -> str:
    txt_path = ref_path.with_suffix(".txt")
    if not txt_path.is_file():
        _run(
            [
                sys.executable,
                "-m",
                "whisper",
                str(ref_path),
                "--language",
                "French",
                "--model",
                WHISPER_MODEL,
                "--output_dir",
                str(refs_dir),
                "--output_format",
                "txt",
            ]
        )
    return txt_path.read_text(encoding="utf-8").strip() if txt_path.is_file() else ""


def _qwen_runtime(mode: str) -> tuple[str, str]:
    if mode == "GPU":
        if not torch.cuda.is_available():
            raise gr.Error(
                "GPU demande, mais PyTorch ne voit pas CUDA. "
                "Il faut installer une version CUDA de PyTorch dans .venv-qwen."
            )
        return "cuda:0", "float16"
    return "cpu", "float32"


def clone_from_upload(
    uploaded_audio: str,
    reference_count: int,
    runtime_mode: str,
    text: str,
) -> tuple[object, ...]:
    started_at = time.perf_counter()
    try:
        outputs, status = _clone_from_upload_impl(uploaded_audio, reference_count, runtime_mode, text)
        elapsed = _format_elapsed(time.perf_counter() - started_at)
        status = f"{status}\nTemps de generation: {elapsed}"
        updates: list[object] = [status]
        for index in range(MAX_RATABLE_OUTPUTS):
            if index < len(outputs):
                path = outputs[index]
                updates.extend(
                    [
                        gr.update(value=path, visible=True, label=f"Sortie {index + 1}"),
                        gr.update(value=path),
                        gr.update(value=None, visible=True),
                        gr.update(visible=True),
                        gr.update(value="", visible=True),
                    ]
                )
            else:
                updates.extend(
                    [
                        gr.update(value=None, visible=False),
                        gr.update(value=""),
                        gr.update(value=None, visible=False),
                        gr.update(visible=False),
                        gr.update(value="", visible=False),
                    ]
                )
        return tuple(updates)
    except gr.Error:
        raise
    except torch.cuda.OutOfMemoryError as exc:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        raise gr.Error(
            "VRAM insuffisante pendant la generation GPU. "
            "Essaie 1 point de reference, ferme les applis qui utilisent le GPU, ou repasse en CPU."
        ) from exc
    except Exception as exc:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        error_path = LOGS_DIR / f"qwen_ui_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        error_path.write_text(traceback.format_exc(), encoding="utf-8")
        raise gr.Error(f"Erreur: {exc}\nTrace complete: {error_path}") from exc


def _clone_from_upload_impl(
    uploaded_audio: str,
    reference_count: int,
    runtime_mode: str,
    text: str,
) -> tuple[list[str], str]:
    source = _store_upload(uploaded_audio)
    reference_count = max(1, int(reference_count))
    if not text.strip():
        raise gr.Error("Entre le texte a faire dire.")
    device, dtype = _qwen_runtime(runtime_mode)

    run_id = _run_id(source)
    refs_dir = REFS_DIR / run_id
    out_dir = OUT_DIR / run_id
    refs_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    durations = [BASE_REFERENCE_DURATION_SECONDS, BASE_REFERENCE_DURATION_SECONDS * 2]
    starts = _reference_starts(source, reference_count, max(durations))
    rows: list[dict[str, object]] = []
    outputs: list[str] = []

    for index, start in enumerate(starts, start=1):
        for duration in durations:
            size_label = "short" if duration == BASE_REFERENCE_DURATION_SECONDS else "long"
            label = f"ref{index}_{size_label}"
            ref_path = _make_reference(source, refs_dir, label, start, duration)
            ref_text = _transcribe_reference(ref_path, refs_dir)
            if not ref_text:
                rows.append(
                    {
                        "index": index,
                        "variant": size_label,
                        "start_seconds": start,
                        "duration_seconds": duration,
                        "reference_audio": str(ref_path),
                        "reference_text": "",
                        "output_audio": "",
                        "status": "transcription vide",
                    }
                )
                continue

            output_path = out_dir / f"{_safe_stem(source)}_{label}_qwen.wav"
            generate_voice_clone(
                ref_audio=ref_path,
                ref_text=ref_text,
                text=text,
                output=output_path,
                device=device,
                dtype=dtype,
                attention=ATTENTION,
                max_new_tokens=MAX_NEW_TOKENS,
            )
            rating_copy_path = _make_rating_copy(output_path)
            outputs.append(str(rating_copy_path))
            rows.append(
                {
                    "index": index,
                    "variant": size_label,
                    "start_seconds": start,
                    "duration_seconds": duration,
                    "reference_audio": str(ref_path),
                    "reference_text": ref_text,
                    "output_audio": str(rating_copy_path),
                    "wav_output_audio": str(output_path),
                    "status": "ok",
                }
            )

    manifest_path = out_dir / f"{_safe_stem(source)}_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "index",
                "variant",
                "start_seconds",
                "duration_seconds",
                "reference_audio",
                "reference_text",
                "output_audio",
                "wav_output_audio",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    status = (
        f"{len(outputs)} sortie(s) generee(s) pour {reference_count} point(s) de reference.\n"
        f"Chaque point produit 2 references: {BASE_REFERENCE_DURATION_SECONDS}s et {BASE_REFERENCE_DURATION_SECONDS * 2}s.\n"
        f"Mode Qwen: {runtime_mode} ({device}, {dtype}).\n"
        f"Run: {run_id}\n"
        f"Source copiee dans: {INPUTS_DIR}\n"
        f"References + transcriptions: {refs_dir}\n"
            f"Sorties WAV, copies MP3 notables + manifest: {out_dir}\n"
        f"Manifest: {manifest_path}"
    )
    return outputs, status


def save_explorer_rating(audio_path: str | None, stars: str | None) -> str:
    if not audio_path:
        raise gr.Error("Aucun audio a noter.")
    if not stars:
        raise gr.Error("Choisis une note avant d'enregistrer.")

    rating = STAR_TO_EXPLORER_RATING.get(stars)
    popm_rating = STAR_TO_ID3_POPM_RATING.get(stars)
    if rating is None or popm_rating is None:
        raise gr.Error(f"Note inconnue: {stars}")

    path = Path(audio_path).expanduser().resolve()
    if not path.is_file():
        raise gr.Error(f"Audio introuvable: {path}")

    errors: list[str] = []

    try:
        from mutagen.id3 import ID3, ID3NoHeaderError, POPM

        try:
            tags = ID3(path)
        except ID3NoHeaderError:
            tags = ID3()

        tags.delall("POPM")
        tags.add(POPM(email=WINDOWS_POPM_EMAIL, rating=popm_rating, count=0))
        tags.save(path, v2_version=3)
    except ImportError as exc:
        raise gr.Error("mutagen est requis pour ecrire les etoiles MP3. Relance .\\scripts\\setup_qwen.ps1.") from exc
    except Exception as exc:
        errors.append(f"ID3 POPM: {exc}")

    try:
        import pythoncom
        from win32com.propsys import propsys, pscon
        from win32com.shell import shellcon

        store = propsys.SHGetPropertyStoreFromParsingName(
            str(path),
            None,
            shellcon.GPS_READWRITE,
            propsys.IID_IPropertyStore,
        )
        store.SetValue(pscon.PKEY_Rating, propsys.PROPVARIANTType(rating, pythoncom.VT_UI4))
        store.Commit()
        del store
        gc.collect()
    except ImportError:
        errors.append("pywin32 manquant")
    except Exception as exc:
        errors.append(f"Property Store Windows: {exc}")

    if errors:
        raise gr.Error(
            f"La note n'a pas pu etre totalement enregistree pour {path.name}.\n"
            + "\n".join(errors)
        )

    return f"Note enregistree dans les etoiles Windows: {stars} ({path})"


CSS = """
.gradio-container {
    max-width: 980px !important;
    margin: 0 auto !important;
}
#main-panel {
    max-width: 900px;
    margin: 0 auto;
}
"""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title=APP_NAME) as demo:
        with gr.Column(elem_id="main-panel"):
            gr.Markdown(f"# {APP_NAME}")
            gr.Markdown(
                "Upload un audio, choisis combien de points de reference tester, puis Qwen genere une sortie courte et une sortie longue pour chaque point."
            )
            gr.Markdown(
                f"**Dossiers**  \n"
                f"Sources uploadees: `{INPUTS_DIR}`  \n"
                f"References et transcriptions: `{REFS_DIR}\\<run>`  \n"
                f"Sorties audio: `{OUT_DIR}\\<run>`"
            )

            uploaded_audio = gr.Audio(label="Audio source", sources=["upload"], type="filepath")
            reference_count = gr.Slider(minimum=1, maximum=12, value=4, step=1, label="Nombre de points de reference")
            runtime_mode = gr.Radio(["CPU", "GPU"], label="Calcul Qwen", value="CPU")
            text = gr.Textbox(label="Texte a dire", value=DEFAULT_TEXT, lines=3)

            run_button = gr.Button("Generer")
            status = gr.Textbox(label="Statut", lines=5, interactive=False)
            gr.Markdown("## Ecouter et noter")
            rating_components: list[gr.components.Component] = []
            for index in range(MAX_RATABLE_OUTPUTS):
                with gr.Group():
                    audio_output = gr.Audio(
                        label=f"Sortie {index + 1}",
                        type="filepath",
                        interactive=False,
                        visible=False,
                    )
                    rating_path = gr.Textbox(visible=False)
                    rating = gr.Radio(
                        STAR_CHOICES,
                        label="Notation Explorateur Windows",
                        value=None,
                        visible=False,
                    )
                    save_rating_button = gr.Button("Enregistrer la note", visible=False)
                    rating_status = gr.Textbox(label="Note", interactive=False, lines=1, visible=False)
                    save_rating_button.click(
                        save_explorer_rating,
                        inputs=[rating_path, rating],
                        outputs=[rating_status],
                    )
                rating_components.extend([audio_output, rating_path, rating, save_rating_button, rating_status])

            run_button.click(
                clone_from_upload,
                inputs=[
                    uploaded_audio,
                    reference_count,
                    runtime_mode,
                    text,
                ],
                outputs=[status, *rating_components],
            )

    return demo


if __name__ == "__main__":
    server_name = os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    build_ui().launch(server_name=server_name, server_port=server_port, inbrowser=True, show_error=True, css=CSS)
