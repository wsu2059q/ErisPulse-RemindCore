moduleInfo = {
    "meta": {
        "name": "RemindCore",
        "version": "1.0.0",
        "description": "通用定时提醒服务模块",
        "author": "WSu2059",
        "license": "MIT",
        "homepage": "",
    },
    "dependencies": {
        "requires": [],
        "optional": ["MessageSender", "OneBotAdapter"],
        "pip": []
    }
}

from .Core import RemindService as Main
