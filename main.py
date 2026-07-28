import os
import datetime
import requests

QYWX_ROBOT_URL = os.getenv("QYWX_ROBOT_URL")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_BIN_ID = os.getenv("JSONBIN_BIN_ID")

# 你的 GitHub Pages 动态护理站地址
PAGE_URL = "https://zhenbinping-boop.github.io/Period-Care-Tracker/"

def get_remote_data():
    """从 JSONBin 远程读取网页打卡的数据（带 3 次失败自动重试机制）"""
    if not JSONBIN_KEY or not JSONBIN_BIN_ID:
        return "2026-07-27", 28, 5, False, False

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest"
    headers = {"X-Master-Key": JSONBIN_KEY}
    
    for attempt in range(3):
        try:
            res = requests.get(url, headers=headers, timeout=10).json()
            record = res.get("record", {})
            return (
                record.get("lastDate", "2026-07-27"),
                int(record.get("cycleDays", 28)),
                int(record.get("periodLength", 5)),
                record.get("factorStress", False),
                record.get("factorSleep", False)
            )
        except Exception as e:
            print(f"⚠️ 第 {attempt + 1} 次尝试连接云端失败: {e}")
            
    print("❌ 3 次尝试连接失败，使用本地备用数据")
    return "2026-07-27", 28, 5, False, False

def send_qywx_notice(content):
    """发送企业微信二人群 Markdown 消息"""
    if not QYWX_ROBOT_URL:
        print("❌ 未配置 QYWX_ROBOT_URL，请检查 GitHub Secrets 设置。")
        return

    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    res = requests.post(QYWX_ROBOT_URL, json=data)
    print(f"✅ 企业微信推送状态: {res.json()}")

def check_and_notify():
    last_date_str, cycle_days, period_length, is_stressed, is_sleep_deprived = get_remote_data()
    
    delay_days = 0
    if is_stressed: delay_days += 2
    if is_sleep_deprived: delay_days += 1

    last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
    today = datetime.date.today()

    next_period_start = last_date + datetime.timedelta(days=cycle_days + delay_days)
    ovulation_day = next_period_start - datetime.timedelta(days=14)
    ovulation_start = ovulation_day - datetime.timedelta(days=5)
    luteal_start = ovulation_day + datetime.timedelta(days=1)

    # 快捷打卡 Markdown 底部按钮
    quick_action_footer = (
        "\n\n---"
        f"\n📲 **微信端快捷打卡（点击即刻更新云端）：**\n"
        f"-[🩸 快捷打卡：经期今天到了]({PAGE_URL}?action=period_today)\n"
        f"-[🎉 快捷打卡：经期今天结束]({PAGE_URL}?action=period_end)\n"
        f"-[⚡ 快捷打卡：今日高压/加班]({PAGE_URL}?action=toggle_stress)\n"
        f"-[🌙 快捷打卡：今日熬夜/失眠]({PAGE_URL}?action=toggle_sleep)\n"
        f"-[🔄 快捷重置影响因子]({PAGE_URL}?action=reset_factors)\n"
        f"-[🌐 打开动态护理站网页]({PAGE_URL})"
    )

    # 1. 排卵期前 1 天提醒
    if today == (ovulation_start - datetime.timedelta(days=1)):
        msg = (
            f"### 🥚 排卵期预警提醒\n"
            f"> **排卵期区间：** {ovulation_start.strftime('%m月%d日')} ~ {(ovulation_day + datetime.timedelta(days=4)).strftime('%m月%d日')}\n\n"
            f"🙋‍♂️ **@男朋友（照顾指南）：**\n"
            f"- 此时她处于雌激素高峰，精力充沛、情绪高涨，适合安排温馨约会或出游！\n"
            f"- 提醒她多补充水分，做好安全避孕措施。\n\n"
            f"🙋‍♀️ **@宝子（温馨贴士）：**\n"
            f"- 明天开始进入排卵期，身体代谢旺盛，保持好心情哦！"
            + quick_action_footer
        )
        send_qywx_notice(msg)

    # 2. 黄体期前 1 天提醒（排卵日当天）
    elif today == ovulation_day:
        msg = (
            f"### 🌧️ 黄体期（PMS经前综合征）预警提醒\n"
            f"> **预计黄体期：** {luteal_start.strftime('%m月%d日')} ~ {(next_period_start - datetime.timedelta(days=1)).strftime('%m月%d日')}\n\n"
            f"🙋‍♂️ **@男朋友（备战指南）：**\n"
            f"- 明天起孕激素上升，容易引发 PMS（皮肤变差、情绪焦虑或易累）。\n"
            f"- 准备一点她爱吃的低糖甜食，多听她倾诉，给足包容与安全感！\n\n"
            f"🙋‍♀️ **@宝子（温馨贴士）：**\n"
            f"- 体内孕激素开始上升，如果觉得疲倦或情绪波动是正常的，今晚早点休息哦！"
            + quick_action_footer
        )
        send_qywx_notice(msg)

    # 3. 经期前 1 天提醒
    elif today == (next_period_start - datetime.timedelta(days=1)):
        msg = (
            f"### ⚠️ 经期倒计时 1 天（痛经预防黄金24小时）\n"
            f"> **预计经期首日：** {next_period_start.strftime('%m月%d日')}\n\n"
            f"🙋‍♂️ **@男朋友（行动清单）：**\n"
            f"- 检查布洛芬/安心裤库存。若有痛经史，见红或微痛第一时间给她服药！\n"
            f"- 准备好 40~45℃ 暖宝宝/热敷带（极速扩张血管降解前列腺素）。\n"
            f"- 今晚将卧室空调调至 18~20℃（降低体温诱导夜间深睡眠）。\n\n"
            f"🙋‍♀️ **@宝子（温馨贴士）：**\n"
            f"- 经期明天即将到来，避免吃冰冷食物，今晚早点睡，所有后勤交给男朋友！"
            + quick_action_footer
        )
        send_qywx_notice(msg)

    # 4. 经期全程每天不同关怀（第 N 天）
    elif last_date <= today <= (last_date + datetime.timedelta(days=period_length - 1)):
        current_day = (today - last_date).days + 1
        
        if current_day == 1:
            care_boy = "阵痛发生第一时间提醒服药，帮她把暖宝宝贴在肚脐下方，端上一杯温热红糖姜茶。"
            care_girl = "宝子辛苦啦！今天子宫正处于缺血痉挛期，多贴热敷，难受就躺着休息哦。"
        elif current_day == 2:
            care_boy = "经血量最大、最疲倦的一天！主动包揽所有家务，今晚卧室开至 18~20℃ 帮她降温深睡眠。"
            care_girl = "今天是经血高峰期，容易疲惫，随时叫男朋友递热水和换暖宝宝！"
        elif current_day == 3:
            care_boy = "痉挛开始缓解！晚餐安排富含铁与 Omega-3 的食物（菠菜/瘦肉/深海鱼）补血。"
            care_girl = "身体在慢慢恢复啦！虽然不那么通了，但依然要避免剧烈运动和受凉哦。"
        else:
            care_boy = f"经期尾声阶段！多给她吃水果补充维C，注意腰腹防风保暖。"
            care_girl = "经期即将结束，气色在变好啦！这几天辛苦啦~"

        msg = (
            f"### 🩸 经期关怀 · 第 {current_day} 天\n"
            f"> **状态：** 经期进行中（预计持续至 {(last_date + datetime.timedelta(days=period_length-1)).strftime('%m月%d日')}）\n\n"
            f"🙋‍♂️ **@男朋友（专属护航）：**\n- {care_boy}\n\n"
            f"🙋‍♀️ **@宝子（专属关怀）：**\n- {care_girl}"
            + quick_action_footer
        )
        send_qywx_notice(msg)

    else:
        print("今日无预警节点，静默守护中。")

if __name__ == "__main__":
    check_and_notify()
