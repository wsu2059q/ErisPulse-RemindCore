# RemindCore

通用定时提醒服务模块，为 ErisPulse 提供跨平台的定时消息推送能力。

## 模块介绍

### RemindCore

提供统一的定时提醒服务，支持多平台消息推送。可用于每日提醒、随机时间提醒等场景，具备良好的扩展性，便于其他模块调用集成。

主要功能：
- 支持固定周期提醒和随机时间提醒
- 自定义过期时间控制任务生命周期（默认永不过期）
- 提供标准接口供其他模块调用
- 支持多平台发送：`yunhu` / `onebot` / `ALL`
- 基于 SDK 的环境配置管理

---

## 接口说明

### 标准接口

#### [AddRemind(target_id, chat_type, message, platform="ALL", expired_at=None)](file://z:\bots\luguan\LuGuanReminder\Core.py#L28-L38)

添加一个固定周期的提醒任务  
参数说明：

- `target_id`: 用户或群组 ID
- `chat_type`: `"user"` 或 `"group"`
- [message](file://z:\bots\luguan\luguan\lib\python3.12\site-packages\ErisPulse\errors.py#L0-L0): 提醒内容文本
- `platform`: 平台标识，建议传入 `"yunhu"` / `"onebot"` / `"ALL"`，默认为 `"ALL"`
- `expired_at`: 提醒任务过期时间，若不传则默认为 `"9999-12-31T23:59:59"` 表示永不过期

#### [AddRandomRemind(target_id, chat_type, messages, interval=(0, 23), platform="ALL", expired_at=None)](file://z:\bots\luguan\LuGuanReminder\Core.py#L40-L50)

添加一个每天随机时间的提醒任务  
参数说明：

- `messages`: 提醒语句列表（将随机选择一条）
- `interval`: 随机时间范围 (小时区间)，默认 `(0, 23)` 表示全天候随机
- `platform`: 同上，默认为 `"ALL"`
- `expired_at`: 同上，默认永不过期

#### [RemoveRemind(target_id, platform="ALL")](file://z:\bots\luguan\LuGuanReminder\Core.py#L52-L56)

移除指定 target 的提醒任务  
参数说明：

- `target_id`: 用户或群组 ID
- `platform`: 可选，表示只移除特定平台下的该目标提醒，默认为 `"ALL"`

#### [ListReminds(platform="ALL")](file://z:\bots\luguan\LuGuanReminder\Core.py#L58-L59)

返回当前所有提醒任务列表  
参数说明：

- `platform`: 可选，表示只列出特定平台下的提醒任务，默认为 `"ALL"`

> ⚠️ **注意**：虽然 `platform` 参数不是强制字段，默认为 `"ALL"`，但**建议开发者根据目标平台明确传入 `"yunhu"` 或 `"onebot"`**，以便更好地控制消息发送路径并避免潜在冲突。

---

## 使用示例

```python
import asyncio
from datetime import datetime, timedelta
from ErisPulse import sdk

# 初始化SDK
sdk.init()

# 获取 RemindCore 实例
remind_core = sdk.RemindCore

async def demo():
    # 示例1：添加一个默认全天随机提醒任务
    remind_core.AddRandomRemind(
        target_id="123456",
        chat_type="user",
        messages=["滴——导管提醒器上线", "今晚安排一下？", "冲冲冲！"]
    )
    print("随机提醒任务已添加")

    # 示例2：添加一个固定提醒任务
    remind_core.AddRemind(
        target_id="789012",
        chat_type="group",
        message="别忘了今天的提醒！",
        platform="yunhu"
    )
    print("固定提醒任务已添加")

    # 示例3：设置自定义过期时间（比如10天后）
    expire_time = datetime.now() + timedelta(days=10)
    remind_core.AddRandomRemind(
        target_id="334455",
        chat_type="user",
        messages=["记得喝水哦"],
        interval=(8, 20),
        platform="onebot",
        expired_at=expire_time
    )
    print("带过期时间的提醒任务已添加")

# 运行示例
await demo()
```

---

## 内部机制说明

### 提醒调度逻辑

- 每分钟检查一次所有注册的提醒目标
- 若达到提醒时间，则自动发送消息
- 消息发送后重新生成下一次提醒时间（随机或固定）
- 若当前时间超过 `expired_at`，则自动移除该提醒任务

### 消息发送逻辑

- 当 `platform == "onebot"` 时，使用对应适配器发送消息
- 当 `platform == "yunhu"` 时，使用对应适配器发送消息
- 当 `platform == "ALL"` 时，尝试所有可用平台发送，优先 OneBot，失败则 Yunhu

---

## 数据结构说明

每个提醒任务存储如下字段：

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `type` | str | 聊天类型，"user" 或 "group" |
| `platform` | str | 平台名称，"yunhu"/"onebot"/"ALL" |
| `last_active` | isoformat(str) | 最后活跃时间（ISO格式字符串） |
| `next_reminder` | isoformat(str) | 下次提醒时间（ISO格式字符串） |
| `mode` | str | 提醒模式，"fixed" 或 "random" |
| [message](file://z:\bots\luguan\luguan\lib\python3.12\site-packages\ErisPulse\errors.py#L0-L0) | str | 固定提醒内容（仅 mode=fixed 时存在） |
| `messages` | list[str] | 随机提醒内容列表（仅 mode=random 时存在） |
| `expired_at` | isoformat(str) | 提醒任务过期时间，默认为 `"9999-12-31T23:59:59"` |

---

## 生命周期管理

在主程序中启动和停止 `RemindCore` 模块：

```python
# main.py
from ErisPulse import sdk
import asyncio

async def main():
    sdk.init()

    # 启动 RemindCore 提醒服务
    if hasattr(sdk, "RemindCore"):
        await sdk.RemindCore.start()
        sdk.logger.info("RemindCore 已启动")

    try:
        # 启动消息监听服务（由当前环境决定使用何种协议）
        if hasattr(sdk, "MessageServer"):
            await sdk.MessageServer.Run()
    finally:
        # 确保退出时清理资源
        if hasattr(sdk, "RemindCore"):
            await sdk.RemindCore.stop()
            sdk.logger.info("RemindCore 已停止")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 参考链接

- [ErisPulse 主库](https://github.com/wsu2059q/ErisPulse/)
- [ErisPulse 开发指南](https://github.com/wsu2059q/ErisPulse/blob/main/%E5%BC%80%E5%8F%91%E6%8C%87%E5%8D%97.md)
