## 介绍

这是一个可为中小型 Python 项目提供配置管理的基类。

配置文件使用 YAML 格式，人类易读。

最简易的配置管理方案，就是单个文件里存放全部的配置，解析 YAML 后，直接用字典、列表去访问。但这样的缺点是没有代码补全，在配置有增删时也无法让程序静态分析，但更为不便的是没法复用一些相对固定的配置。

本库提出的方案，仅通过少量代码，再加上一点编程规范，解决了上述问题：
- 手工将程序所需的配置一一作为属性添加到数据类上，这样实现代码补全，方便静态分析
- 提供解析配置文件的类方法，该方法接收单个配置文件路径，并从中得到其他配置文件路径，最终将这些配置合而为一，实现复用


## 用法

继承基类创建项目的配置类，基类中提供了一些有用的类方法。

```python
# config_handle.py
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from briefconf import BriefConfig

# 请自行更改环境变量的名称
configfile = os.getenv("PROJECT_CONFIG_FILE", default="config.yaml")
merged_config = os.getenv("PROJECT_MERGED_CONFIG", default="")  # 如果要查看合并后的配置，就通过此环境变量传递路径


@dataclass(frozen=True, slots=True)
class Config(BriefConfig):
    """所有配置参数都作为属性，列举在下面。通过类方法初始化配置实例，将配置的获取和配置参数分开放置，程序结构更加清晰。"""
    is_production: bool

    @classmethod
    def load(cls, config_path: str) -> Self:
        configs = cls._load_config(config_path)
        if merged_config:
            Path(merged_config).write_text(BriefConfig._dump(configs))

        return cls(
            is_production=configs["is_production"]
        )


config = Config.load(os.path.abspath(configfile))
```

在其他文件中获得配置参数的值，直接引入实例即可： `from config_handle import config`

---

更具体的使用案例，可以查看 tests/config_handle.py

## 合并规则

1. 配置文件中需要包含键值对 `other_configs_path: []`，里面放上其他配置文件路径。
2. `other_configs_path` 中靠后的配置会覆盖或追加到靠前的配置，具体为：
    - 如果值是字符串、数字、布尔类型，会覆盖靠前的配置；
    - 如果值是列表类型，会追加到后面；
    - 如果值是字典类型，对于重复的字段，根据值的类型，由前面规则决定；新字段会添加进字典。
3. 当前配置文件会覆盖 `other_configs_path` 中合并后的配置。


如下面的简单例子，config.yaml 里引入 pgm_config.yaml，根据字典规则，新字段会添加，因此最终解析后的对象里拥有 `data_dir: config_and_data_files` 和 `is_production: false`。

```yaml
# config.yaml
other_configs_path:
- pgm_config.yaml

is_production: false
```

```yaml
# pgm_config.yaml
data_dir: config_and_data_files
```

---

如果要自定义这个键（other_configs_path）的名称，可以通过修改类成员实现

```python
class CustomConfig(BriefConfig):
    _key4merge_files: ClassVar[str] = "include" # 自定义键名

    is_production: bool

    @classmethod
    def load(cls, config_path: str) -> Self:
        pass
```

## 版本迭代

如果将来 BriefConfig 提供的类方法或行为与之前版本不兼容，会将旧版本保留在子模块中，这样升级后出现问题，只需要从子模块引入即可

```python
from briefconf import BriefConfig

class Config(BriefConfig):
    ...
```

从子模块中引入旧的版本

```python
from briefconf.v1 import BriefConfig

class Config(BriefConfig):
    ...
```
