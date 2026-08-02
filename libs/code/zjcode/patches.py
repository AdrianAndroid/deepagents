"""
运行时品牌补丁应用器

原理：在 Python 模块导入后，动态修改模块的属性
优点：
1. 完全不修改上游源码
2. 100% 接收上游的 bug 修复和新功能
3. 我们的定制永远生效
"""

import importlib
import logging
from typing import Any

from zjcode.brand import PATCH_MAP

logger = logging.getLogger(__name__)


def apply_brand_patches() -> None:
    """应用所有品牌定制补丁

    在应用启动早期调用，确保所有品牌定制在使用前生效。
    对于 main 分支没有的常量，直接注入到模块中。
    """
    applied_count = 0
    failed_count = 0

    for module_path, patches in PATCH_MAP.items():
        try:
            module = importlib.import_module(module_path)

            for name, value in patches.items():
                old_value = getattr(module, name, None)
                if old_value != value:
                    setattr(module, name, value)
                    applied_count += 1
                    logger.debug(
                        f"[zjcode] Patched {module_path}.{name}: "
                        f"{old_value!r} → {value!r}"
                    )

        except ImportError as e:
            logger.warning(
                f"[zjcode] Module {module_path} not found, skipping patches: {e}"
            )
            failed_count += len(patches)
        except Exception as e:
            logger.warning(
                f"[zjcode] Failed to patch {module_path}: {e}"
            )
            failed_count += len(patches)

    if applied_count > 0:
        logger.info(f"[zjcode] Applied {applied_count} brand patches")
    if failed_count > 0:
        logger.warning(f"[zjcode] Failed to apply {failed_count} brand patches")


def patch_path_constants() -> None:
    """修补硬编码的路径常量

    对那些在模块级别就计算好的路径，需要在使用前重新计算。
    延迟到首次访问时调用，避免在包初始化阶段导入重量级模块。
    """
    from pathlib import Path

    try:
        patched = 0

        # 修补 config.py 中的路径常量
        from deepagents_code import config

        if hasattr(config, "_GLOBAL_DOTENV_PATH"):
            old = config._GLOBAL_DOTENV_PATH
            config._GLOBAL_DOTENV_PATH = Path.home() / ".zjcode" / ".env"
            if old != config._GLOBAL_DOTENV_PATH:
                patched += 1

        # 修补 DEFAULT_CONFIG_DIR - 延迟导入 model_config
        from deepagents_code import model_config

        if hasattr(model_config, "DEFAULT_CONFIG_DIR"):
            old = model_config.DEFAULT_CONFIG_DIR
            model_config.DEFAULT_CONFIG_DIR = Path.home() / ".zjcode"
            if old != model_config.DEFAULT_CONFIG_DIR:
                patched += 1

        # 修补 DEFAULT_CONFIG_FILE 和 DEFAULT_CONFIG_PATH
        if hasattr(model_config, "DEFAULT_CONFIG_FILE"):
            old = model_config.DEFAULT_CONFIG_FILE
            model_config.DEFAULT_CONFIG_FILE = Path.home() / ".zjcode" / "config.toml"
            if old != model_config.DEFAULT_CONFIG_FILE:
                patched += 1

        # DEFAULT_CONFIG_PATH 是模块级别计算的，必须单独修补
        if hasattr(model_config, "DEFAULT_CONFIG_PATH"):
            old = model_config.DEFAULT_CONFIG_PATH
            model_config.DEFAULT_CONFIG_PATH = Path.home() / ".zjcode" / "config.toml"
            if old != model_config.DEFAULT_CONFIG_PATH:
                patched += 1

        # 修补 STATE_DIR
        if hasattr(model_config, "STATE_DIR"):
            old = model_config.STATE_DIR
            model_config.STATE_DIR = Path.home() / ".zjcode" / ".state"
            if old != model_config.STATE_DIR:
                patched += 1

        # 修补 media_utils.py 中的 PASTED_MEDIA_DIR
        try:
            from deepagents_code import media_utils

            if hasattr(media_utils, "PASTED_MEDIA_DIR"):
                old = media_utils.PASTED_MEDIA_DIR
                media_utils.PASTED_MEDIA_DIR = Path.home() / ".zjcode" / "pasted"
                if old != media_utils.PASTED_MEDIA_DIR:
                    patched += 1
        except ImportError:
            pass

        # 修补 DEFAULT_STATE_DIR
        if hasattr(model_config, "DEFAULT_STATE_DIR"):
            old = model_config.DEFAULT_STATE_DIR
            model_config.DEFAULT_STATE_DIR = Path.home() / ".zjcode" / ".state"
            if old != model_config.DEFAULT_STATE_DIR:
                patched += 1

        # 修补 sessions.py 中的路径（如果存在）
        try:
            from deepagents_code import sessions

            # 查找所有大写的 _DIR 常量
            for attr in dir(sessions):
                if attr.isupper() and attr.endswith("_DIR") and not attr.startswith("_"):
                    old_path = getattr(sessions, attr)
                    if isinstance(old_path, Path) and ".deepagents" in str(old_path):
                        new_path = Path(str(old_path).replace(".deepagents", ".zjcode"))
                        setattr(sessions, attr, new_path)
                        if old_path != new_path:
                            patched += 1
        except Exception as e:
            logger.debug(f"[zjcode] Failed to patch sessions paths: {e}")

        # 修补 config.py 中 Settings 类的 user_deepagents_dir property
        try:
            from deepagents_code.config import Settings

            # 定义新的 getter
            def user_zjcode_dir_getter(self):
                return Path.home() / ".zjcode"

            # 替换 property
            Settings.user_deepagents_dir = property(user_zjcode_dir_getter)
            patched += 1

            # 替换 get_user_agent_md_path 静态方法
            @staticmethod
            def patched_get_user_agent_md_path(agent_name: str) -> Path:
                return Path.home() / ".zjcode" / agent_name / "AGENTS.md"

            Settings.get_user_agent_md_path = patched_get_user_agent_md_path
            patched += 1

            # 替换 get_agent_dir 方法
            original_get_agent_dir = Settings.get_agent_dir

            def patched_get_agent_dir(self, agent_name: str) -> Path:
                if not self._is_valid_agent_name(agent_name):
                    msg = (
                        f"Invalid agent name: {agent_name!r}. Agent names can only "
                        "contain letters, numbers, hyphens, underscores, and spaces."
                    )
                    raise ValueError(msg)
                return Path.home() / ".zjcode" / agent_name

            Settings.get_agent_dir = patched_get_agent_dir
            patched += 1

        except Exception as e:
            logger.warning(f"[zjcode] Failed to patch Settings paths: {e}")

        if patched > 0:
            logger.info(f"[zjcode] Patched {patched} path constants")
    except Exception as e:
        logger.warning(f"[zjcode] Failed to patch path constants: {e}")


_path_constants_patched = False


def _ensure_path_constants_patched() -> None:
    """延迟修补路径常量，仅在首次调用时执行。"""
    global _path_constants_patched
    if _path_constants_patched:
        return
    _path_constants_patched = True
    patch_path_constants()


def apply_all_patches() -> None:
    """应用所有补丁的入口函数

    品牌补丁在包初始化时应用；路径常量补丁延迟到首次需要时应用，
    避免在 help-only 快速路径上导入 model_config 等重量级模块。
    """
    apply_brand_patches()
