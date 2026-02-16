from os import getenv as env
from typing import Optional, Literal
from pydantic import Field, model_validator
from landserm.config.schemas.main import ValidateOnEnable as BaseModel
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

        if not self.server.startswith("https://"):
            raise ValueError("Notify server must start with https://")
        
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
    
        if not self.server.startswith("https://"):
            raise ValueError("Gotify server must start with https://")

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
    folder_path: str = "/var/log/landserm/"

    @model_validator(mode='after')
    def validate_configuration(self):
        if not isPath(self.folder_path):
            raise ValueError(f"Path to folder: {self.folder_path} does not exist.")
        return self

class DeliveryConfig(BaseModel):
    oled: ConfigOled
    push: ConfigPush
    logs: ConfigLog