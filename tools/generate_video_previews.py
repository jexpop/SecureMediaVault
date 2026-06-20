"""
Standalone tool: generates missing encrypted video previews
(static frame + looping GIF) for videos already in the vault
that don't have them yet (e.g. imported before preview
generation existed).

Usage:
    python\\python.exe -m tools.generate_video_previews
    python\\python.exe -m tools.generate_video_previews --force

--force regenerates previews even for videos that already have
one (e.g. after improving the preview logic, such as skipping a
black intro). Existing "_static.enc"/"_preview.enc" files are
deleted before regenerating.

Run from the project root (same place you run `python -m src.app`).
Does not open any UI window.
"""

import sys
import getpass
import argparse
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.core.config.vault_config import VaultConfig
from src.core.config.vault_session import VaultSession
from src.core.crypto.key_manager import KeyManager
from src.core.crypto.string_crypto_service import StringCryptoService

from src.database.db_bootstrap import DBBootstrap
from src.database.db_manager import SessionLocal
from src.database.models.media_model import Media
from src.database.models.tag_models import Tag  # noqa: F401  (registers relationship target)

from src.core.services.media_category import classify_extension
from src.core.services.video_preview_service import VideoPreviewService


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate (or regenerate) encrypted video previews "
            "for videos already in the vault."
        )
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Regenerate previews even for videos that already "
            "have one (deletes the existing _static.enc / "
            "_preview.enc first)."
        )
    )

    args = parser.parse_args()

    app = QApplication(sys.argv)

    vault_config = VaultConfig()

    if not vault_config.exists():
        print("No vault found (vault/config.json missing). "
              "Run the app first to create one.")
        return

    password = getpass.getpass("Vault password: ")

    if not vault_config.verify_password(password):
        print("Wrong password.")
        return

    # -------------------------
    # SETUP SESSION (needed for filename/media_type decryption)
    # -------------------------
    key_manager = KeyManager()

    metadata_salt = vault_config.get_metadata_salt()

    metadata_key = key_manager.derive_key(
        password=password,
        salt=metadata_salt
    )

    VaultSession.set_password(password)
    VaultSession.set_metadata_key(metadata_key)

    # -------------------------
    # DB BOOTSTRAP (in case tables don't exist yet)
    # -------------------------
    DBBootstrap().ensure_tables()

    session = SessionLocal()

    string_crypto = StringCryptoService()

    preview_service = VideoPreviewService()

    media_items = session.query(Media).all()

    total_videos = 0
    generated = 0
    regenerated = 0
    skipped_existing = 0
    failed = []

    for media in media_items:

        try:
            extension = string_crypto.decrypt(
                media.media_type,
                metadata_key
            )

            filename = string_crypto.decrypt(
                media.original_filename,
                metadata_key
            )

        except Exception:
            print(f"[SKIP] Could not decrypt metadata for "
                  f"media id={media.id} (uuid={media.uuid})")
            continue

        category = classify_extension(extension)

        if category != "video":
            continue

        total_videos += 1

        static_path = Path(media.encrypted_path + "_static.enc")
        preview_path = Path(media.encrypted_path + "_preview.enc")

        already_has_preview = preview_path.exists()

        if already_has_preview and not args.force:
            skipped_existing += 1
            continue

        if already_has_preview and args.force:

            for path in (static_path, preview_path):

                if path.exists():
                    path.unlink()

        label = (
            "[REGENERATING]"
            if already_has_preview
            else "[GENERATING]"
        )

        print(f"{label} {filename} ...", end=" ", flush=True)

        success = preview_service.generate_previews(
            encrypted_video_path=media.encrypted_path,
            password=password,
            extension=extension
        )

        if success:

            print("OK")

            if already_has_preview:
                regenerated += 1
            else:
                generated += 1

        else:
            print("FAILED")
            failed.append(filename)

    session.close()

    # -------------------------
    # SUMMARY
    # -------------------------
    print()
    print("=" * 50)
    print(f"Total videos found:      {total_videos}")
    print(f"Already had preview:     {skipped_existing}")
    print(f"Previews generated:      {generated}")
    print(f"Previews regenerated:    {regenerated}")
    print(f"Failed:                  {len(failed)}")

    if failed:
        print("\nFiles that failed (no preview, will show "
              "generic icon):")

        for name in failed:
            print(f"  - {name}")

    print("=" * 50)


if __name__ == "__main__":
    main()