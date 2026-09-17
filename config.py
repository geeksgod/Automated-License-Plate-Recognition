from dataclasses import dataclass
from pathlib import Path
import tomllib 

@dataclass(frozen=True)
class ModelSettings:
    detector_model: str
    ocr_model: str
    detector_confidence: float
    ocr_device: str

@dataclass(frozen=True)
class AppConfig:
    app_name: str
    debug: bool
    model: ModelSettings
    database: DBSettings 

@dataclass(frozen=True)
class DBSettings:
    conection_string: str 
    db_name: str 
    all_plates: str 
    watch_list: str 


def _load_config(path: Path = Path("config.toml")) -> AppConfig:
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")
        
    with open(path, "rb") as f:
        data = tomllib.load(f)

    return AppConfig(
        app_name=data["app"]["name"],
        debug=data["app"].get("debug", False),
        model=ModelSettings(**data["models"]),
        database=DBSettings(**data["database"])
    )

CONFIG: AppConfig = _load_config()