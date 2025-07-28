"""
Утилита для сохранения файлов скриншотов в директории проектов
"""

from pathlib import Path
from typing import Optional

from setezor.settings import PROJECTS_DIR_PATH


def save_screenshot_file(
    project_id: str, screenshot_bytes: bytes, filename: str, scan_id: Optional[str] = None
) -> str:
    """
    Сохраняет скриншот в директорию проекта и возвращает абсолютный путь к файлу

    Args:
        project_id: ID проекта для создания директории
        screenshot_bytes: Бинарные данные скриншота
        filename: Имя файла для сохранения
        scan_id: ID сканирования для создания поддиректории (опционально)

    Returns:
        str: Абсолютный путь к сохраненному файлу

    Raises:
        Exception: При ошибке создания директории или записи файла
    """
    try:
        if scan_id:
            project_dir = Path(PROJECTS_DIR_PATH) / project_id / scan_id / "screenshots"
        else:
            project_dir = Path(PROJECTS_DIR_PATH) / project_id / "screenshots"

        project_dir.mkdir(parents=True, exist_ok=True)

        file_path = project_dir / filename

        file_path.write_bytes(screenshot_bytes)

        return str(file_path.absolute())

    except (OSError, IOError) as e:
        raise Exception(
            f"Failed to save screenshot file '{filename}' for project '{project_id}': {e}"
        )
    except Exception as e:
        raise Exception(f"Unexpected error saving screenshot file: {e}")
