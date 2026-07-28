import os
import datetime
import requests

SEND_KEY = os.getenv("SERVERCHAN_SENDKEY")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_BIN_ID = os.getenv("JSONBIN_BIN_ID")

def get_remote_data():
    """从 JSONBin 远程读取网页打卡的数据"""
    if not JSONBIN_KEY or not JSONBIN_BIN_ID:
        return "2026-07-27", 28, 5, False, False

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest"
    headers = {"X-Master-Key": JSONBIN_KEY}
    
    try:
        res = requests.get(url, headers=headers).json()
        record = res.get("record", {})
        return (
            record.get("lastDate", "2026-07-27"),
            int(record.get("cycleDays", 28)),
            int(record.get("periodLength", 5)),
            record.get("factorStress", False),
            record.get("factorSleep", False)
        )
    except Exception as e:
        print(f"读取远程数据失败，使用默认值: {e}")
        return "2026-07-27", 28, 5, False, False

def send_wechat_notice(title, content):
    if not SEND_KEY:
        print("❌ 未找到 SEND_KEY")
        return
    url = f"https://sctapi.ftqq.com/{SEND_KEY}.send"
    res = requests.post(url, data={"title": title, "desp": content})
    print(f"✅ 推送状态: {res.json()}")

def check_and_notify():
    last_date_str, cycle_days, period_length, is_stressed, is_sleep_deprived = get_remote_data()
    
    # 1. 动态延迟计算
    delay_days = 0
    if is_stressed: delay_days += 2
    if is_sleep_deprived: delay_days += 1

    last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
    today = datetime.date.today()

    # 2. 核心生理节点计算
    # 下次经期预测首日
    next_period_start = last_date + datetime.timedelta(days=cycle_days + delay_days)
    # 排卵日（下次经期前14天）
    ovulation_day = next_period_start - datetime.timedelta(days=14)
    # 排卵期起始日（排卵日前5天）
    ovulation_start = ovulation_day - datetime.timedelta(days=5)
    # 黄体期起始日（排卵日后第1天）
    luteal_start = ovulation_day + datetime.timedelta(days=1)

    print(f"今天是: {today} | 上次首日: {last_date} | 下次预计: {next_period_start}")

    # =========================================================================
    # 🔔 条件 1：排卵期前 1 天提醒
    # =========================================================================
    if today == (ovulation_start - datetime.timedelta(days=1)):
        title = "🥚 贴心提醒：宝子明天进入排卵期（易孕窗口）"
        content = (
            f"**排卵期区间：** {ovulation_start.strftime('%m月%d日')} ~ {(ovulation_day + datetime.timedelta(days=4)).strftime('%m月%d日')}\n\n"
            "**💡 男朋友护理备忘：**\n"
            "1. 🌸 **代谢旺盛：** 此时雌激素达到高峰，她精力较充沛，情绪也比较高涨，适合安排约会/出游。\n"
            "2. 💧 **提醒喝水：** 提醒她多补充水分，保持作息规律。\n"
            "3. ⚠️ **避秘/安全：** 若无备孕计划，请务必做好安全避孕措施！"
        )
        send_wechat_notice(title, content)

    # =========================================================================
    # 🔔 条件 2：黄体期前 1 天提醒（即排卵日当天）
    # =========================================================================
    elif today == ovulation_day:
        title = "🌧️ 贴心提醒：宝子明天进入黄体期（PMS预警期）"
        content = (
            f"**预计黄体期：** {luteal_start.strftime('%m月%d日')} ~ {(next_period_start - datetime.timedelta(days=1)).strftime('%m月%d日')}\n\n"
            "**💡 男朋友护理备忘（孕激素上升期）：**\n"
            "1. 🍫 **情绪多包容：** 黄体期孕激素上升，易引发经前综合征（PMS），可能出现皮肤变差、情绪波动或焦虑。\n"
            "2. 🍰 **甜食与拥抱：** 准备一点她爱吃的低糖甜食，多听她倾诉，给足安全感。\n"
            "3. 🛌 **避免熬夜：** 提醒她早睡，熬夜会加重 HPA 轴应激导致经期紊乱[cite: 1]！"
        )
        send_wechat_notice(title, content)

    # =========================================================================
    # 🔔 条件 3：经期前 1 天提醒（黄金预备期）
    # =========================================================================
    elif today == (next_period_start - datetime.timedelta(days=1)):
        title = "⚠️ 紧急备战：宝子的经期明天即将到达！"
        content = (
            f"**预计经期首日：** {next_period_start.strftime('%m月%d日')}\n\n"
            "**💡 循证痛经预防备忘（黄金24小时）：**\n"
            "1. 💊 **早期预防给药：** 检查布洛芬/双氯芬酸库存。若有痛经史，见红或微痛第一时间服用，阻断前列腺素爆发[cite: 1]！\n"
            "2. ♨️ **备好热敷贴：** 准备好 40~45℃ 暖宝宝（扩张血管促进前列腺素代谢，镇痛效果堪比止痛药）[cite: 1]。\n"
            "3. 🌙 **卧室物理降温：** 今晚卧室空调调至 18~20℃（降低黄体期偏高体温，促进夜间深睡眠）[cite: 1]。\n"
            "4. 📦 **检查卫生用品：** 检查安心裤/夜用卫生巾库存是否充足。"
        )
        send_wechat_notice(title, content)

    # =========================================================================
    # 🔔 条件 4：经期全程每天不同关怀（根据经期第 N 天区别提醒）
    # =========================================================================
    elif last_date <= today <= (last_date + datetime.timedelta(days=period_length - 1)):
        current_day = (today - last_date).days + 1
        
        # --- 经期第 1 天 ---
        if current_day == 1:
            title = "🩸 经期关怀 · 第 1 天：强效镇痛与强力守护"
            content = (
                "**💡 循证护理重点（子宫缺血与前列腺素高峰期）：**\n"
                "1. 💊 **及时服药：** 出现阵痛第一时间吃布洛芬（连续按时服用，阻断痉挛）[cite: 1]。\n"
                "2. ♨️ **持续热敷下腹：** 把暖宝宝贴在她肚脐下方（加速前列腺素冲刷，极速止痛）[cite: 1]。\n"
                "3. 🍵 **忌生冷忌咖啡因：** 端上一杯温热红糖姜茶，严禁冷饮与咖啡[cite: 1]。\n"
                "4. 💆 **按摩三阴交：** 顺着脚踝内侧往上四指处帮她轻柔按摩[cite: 1]。"
            )
        # --- 经期第 2 天 ---
        elif current_day == 2:
            title = "🩸 经期关怀 · 第 2 天：经血高峰与夜间安睡"
            content = (
                "**💡 循证护理重点（量最大、最易疲倦期）：**\n"
                "1. 🌙 **今夜助眠降温：** 睡觉前把卧室空调开到 18~20℃（帮助降低体温，引导慢波深睡眠）[cite: 1]。\n"
                "2. 🛋️ **主动承担家务：** 让她平躺休息，主动接管所有家务，减少她站立和受凉[cite: 1]。\n"
                "3. 🍵 **补充清淡温饮：** 准备温热豆浆或红豆汤，松弛子宫平滑肌[cite: 1]。"
            )
        # --- 经期第 3 天 ---
        elif current_day == 3:
            title = "🩸 经期关怀 · 第 3 天：疼痛缓解与营养补血"
            content = (
                "**💡 循证护理重点（痉挛减轻、身体恢复期）：**\n"
                "1. 🥗 **补铁与 Omega-3：** 晚餐安排富含铁元素与 Omega-3 的食物（如瘦肉、菠菜、深海鱼）[cite: 1]。\n"
                "2. 🚶‍♀️ **避免剧烈运动：** 疼痛虽已减轻，但子宫内膜仍在修复，陪她散散步即可[cite: 1]。\n"
                "3. 🫂 **情绪安抚：** 孕激素撤退期容易疲惫，多抱抱她，听她说话[cite: 1]。"
            )
        # --- 经期第 4 天及以后 ---
        else:
            title = f"🩸 经期关怀 · 第 {current_day} 天：尾声滋养与体力恢复"
            content = (
                f"**预计经期还剩 {period_length - current_day + 1} 天：**\n\n"
                "**💡 循证护理重点：**\n"
                "1. 🍊 **补充维生素 C 与镁：** 多吃水果补充维C，促进铁吸收与神经传导恢复[cite: 1]。\n"
                "2. 🦺 **注意保暖防止受凉：** 尾声阶段子宫颈尚未完全闭合，注意腰腹防风防凉[cite: 1]。\n"
                "3. 🎉 **夸夸与关怀：** 辛苦照顾了她一整个周期，宝子的身体正在快速恢复活力[cite: 1]！"
            )
        
        send_wechat_notice(title, content)

    else:
        print("今日不在任何预警/经期节点内，静默守护中。")

if __name__ == "__main__":
    check_and_notify()
