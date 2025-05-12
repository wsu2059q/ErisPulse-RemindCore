moduleInfo = {
    "meta": {
        "name": "RemindCore",
        "version": "1.1.1",
        "description": "通用定时提醒服务模块",
        "author": "WSu2059",
        "license": "MIT",
        "homepage": "https://github.com/wsu2059q/ErisPulse-RemindCore",
    },
    "dependencies": {
        "requires": [],
        "optional": ["YunhuMessageSender", "OneBotAdapter"],
        "pip": []
    }
}

from .Core import RemindService as Main
