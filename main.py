import os
import datetime
import requests

SEND_KEY = os.getenv("SERVERCHAN_SENDKEY")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_BIN_ID = os.getenv("JSONBIN_BIN_ID")

def get_remote_data():
    """从 JSONBin 远程读取网页打卡的数据"""
    if not JSONBIN_KEY or not JSONBIN_BIN_ID:
        # 如果未配置在线数据库，默认返回基准值
        return "2026-07-10", 28, False, False

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest"
    headers = {"X-Master-Key": JSONBIN_KEY}
    
    try:
        res = requests.get(url, headers=headers).json()
        record = res.get("record", {})
        return (
            record.get("lastDate", "2026-07-10"),
            int(record.get("cycleDays", 28)),
            record.get("factorStress", False),
            record.get("factorSleep", False)
        )
    except Exception as e:
        print(f"读取远程数据失败，使用默认值: {e}")
        return "2026-07-10", 28, False, False

def send_wechat_notice(title, content):
    if not SEND_KEY:
        print("❌ 未找到 SEND_KEY")
        return
    url = f"https://sctapi.ftqq.com/{SEND_KEY}.send"
    requests.post(url, data={"title": title, "desp": content})

def check_and_notify():
    last_date_str, cycle_days, is_stressed, is_sleep_deprived = get_remote_data()
    
    # 动态修正天数
    delay_days = 0
    if is_stressed: delay_days += 2
    if is_sleep_deprived: delay_days += 1

    last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
    target_date = last_date + datetime.timedelta(days=cycle_days + delay_days)
    
    # 预测窗口：[target - 1天, target + 2天]
    win_start = target_date - datetime.timedelta(days=1)
    win_end = target_date + datetime.timedelta(days=2)
    
    today = datetime.date.today()
    days_to_window = (win_start - today).days

    print(f"今天是 {today}，预计经期窗口：{win_start} ~ {win_end}，距离窗口起始还有 {days_to_window} 天")

    # 进入窗口前 2 天触发预警推送
    if days_to_window == 2:
        title = "🌸 贴心预警：宝子即将在 2 天内进入经期窗口"
        content = (
            f"**预计经期区间：** {win_start.strftime('%m月%d日')} ~ {win_end.strftime('%m月%d日')}\n"
            f"*(考虑打卡影响因子，预测已动态调整)*\n\n"
            "**💡 循证疼痛与睡眠关怀清单：**\n"
            "1. 💊 **早期预防给药：** 检查布洛芬/双氯芬酸库存，出现微痛或见红第一时间服用，阻断前列腺素爆发[cite: 1]！\n"
            "2. ♨️ **40~45℃ 物理热疗：** 准备好热敷贴（扩张血管促进前列腺素冲刷代谢，镇痛效果堪比止痛药）[cite: 1]。\n"
            "3. 🌙 **今夜助眠降温：** 卧室空调可调至 18~20℃（帮助降低黄体期偏高体温，诱导深睡眠）[cite: 1]。\n"
            "4. 🥗 **营养与避忌：** 补充 Omega-3/镁剂温饮（松弛平滑肌）[cite: 1]，严禁咖啡因与酒精[cite: 1]。\n"
            "5. 🫂 **情绪包容：** 避免熬夜，多给拥抱，防止睡眠剥夺导致痛觉敏化[cite: 1]！"
        )
        send_wechat_notice(title, content)

if __name__ == "__main__":
    check_and_notify()
