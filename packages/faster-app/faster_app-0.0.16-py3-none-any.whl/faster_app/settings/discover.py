"""
自动发现 apps 目录下的 models 模块
"""

from typing import Any, Dict
from pydantic_settings import BaseSettings
from faster_app.base import DiscoverBase


class SettingsDiscover(DiscoverBase):
    """配置发现器"""

    INSTANCE_TYPE = BaseSettings

    TARGETS = [
        {
            "directory": "config",
            "filename": None,
            "skip_dirs": ["__pycache__"],
            "skip_files": [],
        },
        {
            "directory": f"{DiscoverBase.FASTER_APP_PATH}/settings/builtins",
            "filename": "settings.py",
            "skip_dirs": ["__pycache__"],
            "skip_files": [],
        },
    ]

    def merge(self) -> BaseSettings:
        """合并配置: 使用用户配置覆盖内置配置"""
        default_settings = BaseSettings
        user_settings = []

        configs = self.discover()

        for config in configs:
            if type(config).__name__ == "DefaultSettings":
                default_settings = config
            else:
                user_settings.append(config)

        default_dict = default_settings.model_dump()

        for user_setting in user_settings:
            user_dict = user_setting.model_dump()
            # 覆盖所有存在的属性
            for key, value in user_dict.items():
                default_dict[key] = value

        # 为动态字段创建类型注解
        annotations = {}
        class_dict = {"__module__": __name__}

        for key, value in default_dict.items():
            # 根据值的类型推断注解
            if isinstance(value, str):
                annotations[key] = str
            elif isinstance(value, int):
                annotations[key] = int
            elif isinstance(value, bool):
                annotations[key] = bool
            elif isinstance(value, dict):
                annotations[key] = Dict[str, Any]
            else:
                annotations[key] = Any

            # 设置默认值
            class_dict[key] = value

        # 添加类型注解
        class_dict["__annotations__"] = annotations

        # 动态创建 BaseSettings 的子类
        MergedSettings = type("MergedSettings", (BaseSettings,), class_dict)

        # 创建并返回实例
        merged_settings = MergedSettings()
        return merged_settings
