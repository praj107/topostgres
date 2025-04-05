import json
import os
from dataclasses import dataclass
from typing import Optional

# ----- Common Config Class -----

@dataclass
class DatabaseConfig:
    host: str
    user: str
    password: str
    port: int
    database: Optional[str] = None  # For MySQL
    dbname: Optional[str] = None    # For Postgres

    def unpack_mysql(self) -> dict:
        return {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "port": self.port,
            "database": self.database,
        }
    
    def unpack_postgres(self) -> dict:
        return {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "port": self.port,
            "dbname": self.dbname,
        }

# ----- Load and Parse Config -----

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

with open(CONFIG_PATH) as f:
    raw_config = json.load(f)  # ✅ No [0] here — it's a plain dict

# Map to shared class
MYSQL = DatabaseConfig(**raw_config["mysql"])
POSTGRES = DatabaseConfig(**raw_config["postgres"])
