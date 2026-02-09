import warnings
import requests
from os import getenv as env
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator
from landserm.config.validators import isPath

class ConfigOled(BaseModel):
    enabled: bool
    driver: Literal["sh1106", "ssd1306", "ssd1331"]
    port: Optional[int] = 1
    address: Literal["0x3C", "0x3D"] = "0x3C"
    device: str
    width: int
    height: int
    font_size: int = Field(default=11, ge=9, le=12)

class PushNotify(BaseModel):
    enabled: bool
    server: str

    @model_validator(mode='after')
    def validate_configured(self):
        if not self.enabled:
            return self
            
        try:
            response = requests.get(self.server, timeout=2)
            if response.status_code != 200:
                warnings.warn(f"Notify server {self.server} responded with {response.status_code}")
        except requests.RequestException as e:
            warnings.warn(f"Couldn't connect to ntfy server {self.server}: {e}")
        
        return self

class PushGotify(BaseModel):
    enabled: bool
    server: str
    app_token: str = Field(default_factory=lambda: env("GOTIFY_TOKEN", ""))

    @model_validator(mode='after')
    def validate_configuration(self):
        if not self.enabled:
            return self
        
        if not self.app_token:
            raise ValueError("Gotify is enabled but GOTIFY_TOKEN is not set, and it is needed to work properly.")
    
        try:
            response = requests.get(f"{self.server}/health", timeout=2)
            if response.status_code != 200:
                warnings.warn(f"Gotify server {self.server} responded with {response.status_code}")
        except requests.RequestException as e:
            warnings.warn(f"Couldn't connect to Gotify server {self.server}: {e}")

        return self

        
class PushDiscordWebhook(BaseModel):
    enabled: bool
    url: str = Field(default_factory=lambda: env("DISCORD_WEBHOOK_URL", ""))

    @model_validator(mode='after')
    def validate_configuration(self):
        if not self.enabled:
            return self
            
        if not self.url:
            raise ValueError("Webhook is enabled but DISCORD_WEBHOOK_URL is not set, and it is needed to work properly.")

        if not self.url.startswith("https://discord.com/api/webhooks"):
            raise ValueError("Webhook URL must start with https://discord.com/api/webhooks")
        return self
        

class ConfigPush(BaseModel):
    ntfy: Optional[PushNotify] = None
    gotify: Optional[PushGotify] = None
    webhook: Optional[PushDiscordWebhook] = None

class ConfigLog(BaseModel):
    enabled: bool
    folder_path: str = "/var/log/"

    @model_validator(mode='after')
    def validate_configuration(self):
        if not self.path.endswith("/"):
            raise ValueError("Path should end with \"/\", it is the folder to the logs.")
        if not isPath(self.path):
            raise ValueError("Invalid path.")

class DeliveryConfig(BaseModel):
    oled: ConfigOled
    push: ConfigPush
    logs: ConfigLog