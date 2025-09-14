import os
import sys
import time
import json
import importlib.util
from pathlib import Path
import discord
from discord.ext import commands

spinner_frames = ["|", "/", "-", "\\"]
imported_modules = {}
imported_jsons = {}
already_loaded = False


def run_python_file(file_path: Path, bot):
    """Dynamically import and run a Python file if it defines start()."""
    try:
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "start") and callable(module.start):
            module.start(bot=bot)

        imported_modules[file_path.stem] = str(file_path)

    except Exception as e:
        imported_modules[file_path.stem] = f"ERROR: {e}"


def run_json_file(file_path: Path):
    """Register a JSON file by name + path."""
    try:
        imported_jsons[file_path.stem] = str(file_path)
    except Exception as e:
        imported_jsons[file_path.stem] = f"ERROR: {e}"


def spinner_loader(task_name, index, total, action):
    """Show rotating spinner for at least 0.5s while performing an action."""
    start_time = time.time()
    while time.time() - start_time < 0.5:
        for frame in spinner_frames:
            sys.stdout.write(f"\r{frame} Loading {task_name} ({index}/{total})")
            sys.stdout.flush()
            time.sleep(0.1)
    # Clear line after done
    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()
    action()


def boot(TOKEN: str, json_path: str = "boot.json"):
    """
    Boot function:
    - Starts Discord bot
    - Loads Python & JSON files
    - Saves results to boot.json
    - Returns bot instance
    """
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="!", intents=intents)

    parent_dir = Path(__file__).resolve().parent
    json_dir = parent_dir / "json"

    @bot.event
    async def on_ready():
        global already_loaded
        if already_loaded:
            return

        print(f"✅ Bot connected as {bot.user}")
        already_loaded = True

        # Python files
        all_py_files = [
            Path(root) / file
            for root, _, files in os.walk(parent_dir)
            for file in files
            if file.endswith(".py") and file != Path(__file__).name
        ]

        for i, file_path in enumerate(all_py_files, 1):
            spinner_loader(file_path.name, i, len(all_py_files),
                           lambda fp=file_path: run_python_file(fp, bot))

        # JSON files
        json_files = list(json_dir.glob("*.json")) if json_dir.exists() else []

        for i, file_path in enumerate(json_files, 1):
            spinner_loader(file_path.name, i, len(json_files),
                           lambda fp=file_path: run_json_file(fp))

        # Save results to boot.json
        data = {
            "Components": imported_modules,
            "JsonFiles": imported_jsons
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print("💾 boot.json updated with loaded components.")

    bot.run(TOKEN)
    return bot
