import asyncio
import random
from datetime import datetime, timedelta

class RemindService:
    def __init__(self, sdk):
        self.sdk = sdk
        self.logger = sdk.logger
        self.env = sdk.env

        self.reminders = self.env.get("reminders", {})
        self.task_handle = None

    async def start(self):
        if not self.task_handle:
            self.task_handle = asyncio.create_task(self._reminder_task())
            self.logger.info("提醒服务已启动")

    async def stop(self):
        if self.task_handle:
            self.task_handle.cancel()
            try:
                await self.task_handle
            except asyncio.CancelledError:
                pass
            self.task_handle = None
            self.logger.info("提醒服务已停止")

    def AddRemind(self, target_id, chat_type, message, platform="ALL", expired_at=None):
        try:
            now = datetime.now().isoformat()
            self.reminders[target_id] = {
                "type": chat_type,
                "platform": platform,
                "last_active": now,
                "next_reminder": self._generate_next_fixed_time().isoformat(),
                "message": message,
                "mode": "fixed",
                "expired_at": expired_at.isoformat() if expired_at else "9999-12-31T23:59:59"
            }
            self.env.set("reminders", self.reminders)
            self.logger.info(f"添加固定提醒: {target_id}")
        except Exception as e:
            self.logger.error(f"添加固定提醒失败: {e}")

    def AddRandomRemind(self, target_id, chat_type, messages, interval=(0, 23), platform="ALL", expired_at=None):
        try:
            now = datetime.now().isoformat()
            self.reminders[target_id] = {
                "type": chat_type,
                "platform": platform,
                "last_active": now,
                "next_reminder": self._generate_next_random_time(interval).isoformat(),
                "messages": messages,
                "mode": "random",
                "expired_at": expired_at.isoformat() if expired_at else "9999-12-31T23:59:59"
            }
            self.env.set("reminders", self.reminders)
            self.logger.info(f"添加随机提醒: {target_id}")
        except Exception as e:
            self.logger.error(f"添加随机提醒失败: {e}")
        
    def RemoveRemind(self, target_id, platform="ALL"):
        try:
            removed = False
            if target_id in self.reminders:
                info = self.reminders[target_id]

                if platform == "ALL" or info["platform"] == platform:
                    del self.reminders[target_id]
                    removed = True
                    self.logger.info(f"移除提醒: {target_id} (platform={platform})")

            if removed:
                self.env.set("reminders", self.reminders)
        except Exception as e:
            self.logger.error(f"移除提醒失败: {e}")
    
    def ListReminds(self, platform="ALL"):
        try:
            if platform == "ALL":
                return list(self.reminders.keys())
            else:
                return [target_id for target_id, info in self.reminders.items() if info["platform"] == platform]
        except Exception as e:
            self.logger.error(f"列出提醒失败: {e}")
            return []
    def _generate_next_fixed_time(self):
        now = datetime.now()
        return now + timedelta(days=1)

    def _generate_next_random_time(self, interval):
        now = datetime.now()
        next_time = now + timedelta(days=1)
        hour = random.randint(*interval)
        minute = random.randint(0, 59)
        return next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

    async def _reminder_task(self):
        while True:
            try:
                now = datetime.now()
                for target_id, info in list(self.reminders.items()):
                    expired_at = datetime.fromisoformat(info["expired_at"])
                    if now > expired_at:
                        self.logger.info(f"提醒任务已过期: {target_id}")
                        self.RemoveRemind(target_id)
                        continue

                    next_reminder = datetime.fromisoformat(info["next_reminder"])
                    if now >= next_reminder:
                        message = info.get("message")
                        if not message and "messages" in info:
                            message = random.choice(info["messages"])
                        await self._send_message(target_id, info["type"], message, info["platform"])

                        if info["mode"] == "fixed":
                            info["next_reminder"] = self._generate_next_fixed_time().isoformat()
                        elif info["mode"] == "random":
                            info["next_reminder"] = self._generate_next_random_time((0, 23)).isoformat()

                self.env.set("reminders", self.reminders)
                await asyncio.sleep(60)

            except Exception as e:
                self.logger.error(f"提醒任务异常: {e}")
                await asyncio.sleep(60)
    async def _send_message(self, target_id, target_type, message, platform="ALL"):
        try:
            sent = False

            if platform in ["onebot", "ALL"] and hasattr(self.sdk, "OneBotAdapter") and target_type in ["user", "group"]:
                action = "send_private_msg" if target_type == "user" else "send_group_msg"
                params = {"user_id" if target_type == "user" else "group_id": target_id, "message": message}
                await self.sdk.OneBotAdapter.send_action(action, params)
                self.logger.info(f"[OneBot] 已发送提醒到 {target_type}({target_id})")
                sent = True

            if platform in ["yunhu", "ALL"] and hasattr(self.sdk, "MessageSender"):
                await self.sdk.MessageSender.Text(recvId=target_id, recvType=target_type, content=message)
                self.logger.info(f"[Yunhu] 已发送提醒到 {target_type}({target_id})")
                sent = True

            if not sent:
                self.logger.warning("未找到任何可用的消息发送模块或平台不匹配")

        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")