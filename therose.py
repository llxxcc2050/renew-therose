import os
import time
import requests
from seleniumbase import SB

# ==================== 配置区域 ====================
TELEGRAM_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8955581661:AAERfToZyB1RpAMRVQx1gx0lasNxjBJeLUQ")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID", "7816469203")

EMAIL = os.getenv("THEROSE_EMAIL", "llxxcc2050@gmail.com")
PASSWORD = os.getenv("THEROSE_PASSWORD", "Llxxcc1214")
SERVER_ID = os.getenv("THEROSE_SERVER_ID", "30c38986") 

PANEL_LOGIN_URL = "https://panel.therose.cloud/auth/login"
SERVER_CONSOLE_URL = f"https://panel.therose.cloud/server/{SERVER_ID}"
# ==================================================

def send_tg_notification(message):
    """发送 Telegram 通知"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or TELEGRAM_BOT_TOKEN.startswith("你的"):
        print("⚠️ 未配置有效的 Telegram Token 或 Chat ID，跳过发送通知。")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            print("📨 Telegram 通知已发送")
        else:
            print(f"❌ Telegram 通知发送失败: {response.text}")
    except Exception as e:
        print(f"❌ 发送 TG 通知时发生异常: {e}")

def run_automation():
    msg_logs = []
    def log(text):
        print(text)
        msg_logs.append(text)

    log("🚀 启动浏览器")
    
    with SB(uc=True, headless=True, proxy="socks5://127.0.0.1:1080") as sb:
        try:
            log("⚙️ 代理已启用: socks5://127.0.0.1:1080")
            
            # 检查出口IP
            try:
                sb.open("https://api.ipify.org")
                ip = sb.get_text("body")
                log(f"🎯 当前出口IP: {ip}")
            except Exception:
                log("⚠️ 无法获取出口IP，继续执行主流程...")

            # 1. 智能登录主站流程
            log("🌐 打开登录主页面...")
            sb.open("https://therose.cloud/login")
            sb.sleep(6)  # 留出充足时间让 Cloudflare 挑战盾完全加载

            # 【新增：强力破除 Cloudflare / Turnstile 拦截盾】
            log("🛡 检测并尝试通过人机验证挑战盾...")
            try:
                # 尝试穿透寻找常见的 Turnstile 验证组件并模拟点击
                if sb.is_element_present("iframe[src*='turnstile']"):
                    log("⚡ 发现 Turnstile 验证框，正在尝试自动绕过...")
                    sb.driver.uc_switch_to_frame("iframe[src*='turnstile']")
                    sb.click("#challenge-stage")
                    sb.driver.switch_to.default_content()
                    sb.sleep(4)
                elif sb.is_element_present("#challenge-running"):
                    log("⚡ 发现基础浏览器挑战，等待自动放行...")
                    sb.sleep(6)
            except Exception as shield_err:
                log(f"⚠️ 破盾模块提示（若页面已正常加载可忽略）: {shield_err}")
            
            log("⏳ 开始多策略匹配邮箱输入框...")
            # 兼容多种可能的表单属性命名
            email_selectors = ['input[type="email"]', 'input[name="email"]', 'input[name="username"]']
            active_email_sel = None
            
            for sel in email_selectors:
                if sb.is_element_visible(sel):
                    active_email_sel = sel
                    break
            
            if not active_email_sel:
                log("⚠️ 常规可见性检查未通过，尝试使用强力显式等待...")
                # 最终兜底尝试等待 15 秒
                sb.wait_for_element('input[type="email"], input[name="email"]', timeout=15)
                active_email_sel = 'input[type="email"]' if sb.is_element_present('input[type="email"]') else 'input[name="email"]'

            log("📧 填写邮箱...")
            sb.type(active_email_sel, EMAIL)
            
            log("🔑 填写密码...")
            password_sel = 'input[type="password"]', 'input[name="password"]'
            active_pwd_sel = password_sel[0] if sb.is_element_present(password_sel[0]) else password_sel[1]
            sb.type(active_pwd_sel, PASSWORD)
            
            log("⏳ 等待验证 Token 注入生效...")
            sb.sleep(3)
            
            log("🔑 点击登录按钮...")
            login_btn = 'button[type="submit"], button:contains("Login"), button:contains("登录")'
            sb.wait_for_element(login_btn, timeout=10)
            sb.click(login_btn)
            sb.sleep(6)
            
            log("✅ 登录动作已执行，进入 Dashboard")
            
            # 2. 续期流程
            log("📄 开始续期流程...")
            extend_btn_selector = 'button:contains("Extend"), button:contains("续期"), a:contains("Extend")'
            if sb.is_element_visible(extend_btn_selector):
                sb.click(extend_btn_selector)
                log("🎉 成功点击续期按钮！")
                sb.sleep(3)
            else:
                log("⏳ 未到续期时间，Extend 按钮尚未出现（一般到期前半小时开放），本次跳过。")

            # 3. 服务器重启流程 (Pterodactyl 面板)
            log("🔄 开始检查并执行服务器重启...")
            log(f"🔄 准备进入服务器面板: {SERVER_CONSOLE_URL}")
            sb.open(SERVER_CONSOLE_URL)
            sb.sleep(6)
            
            # 检测是否被拦截在面板登录页
            if "auth/login" in sb.get_current_url() or sb.is_element_present('input[name="username"]'):
                log("🔒 检测到控制面板需要独立登录，正在尝试自动输入账号密码...")
                sb.wait_for_element('input[name="username"]', timeout=10)
                sb.type('input[name="username"]', EMAIL)
                sb.type('input[name="password"]', PASSWORD)
                sb.click('button[type="submit"]')
                sb.sleep(6)
                # 再次强行进入目标服务器控制台
                sb.open(SERVER_CONSOLE_URL)
                sb.sleep(5)
                
            # 再次检查是否停留在主列表页，若是则强制纠正
            if "server/" not in sb.get_current_url():
                log("🔀 检测到停留在主列表页，正在强制进入目标服务器控制台...")
                sb.open(SERVER_CONSOLE_URL)
                sb.sleep(5)

            log("🟢 服务器在线，准备点击 Restart 按钮...")
            
            # 多策略强力按钮匹配与点击方案
            selectors = [
                'button:contains("Restart")', 
                'button:contains("restart")',
                'button:contains("重启")',
                'button[class*="power"]',
                'button[class*="restart"]',
                '//button[contains(., "Restart")]',
                '//button[contains(., "重启")]',
                'div:contains("Restart")',
                'span:contains("Restart")'
            ]
            
            btn_clicked = False
            for sel in selectors:
                try:
                    if sel.startswith('//'):
                        sb.wait_for_element_present(sel, by="xpath", timeout=2)
                        sb.click(sel, by="xpath")
                    else:
                        sb.wait_for_element_present(sel, timeout=2)
                        sb.click(sel)
                    log(f"✅ 成功通过选择器 [{sel}] 点击了 Restart 按钮！")
                    btn_clicked = True
                    break
                except Exception:
                    continue
            
            # JS 强行穿透点击兜底
            if not btn_clicked:
                log("⚠️ 常规文本精确定位未找到，尝试通过注入高级 JavaScript 强行触发点击...")
                js_click_script = """
                const tags = Array.from(document.querySelectorAll('button, div, span, a'));
                const target = tags.find(el => {
                    if(!el.textContent) return false;
                    const text = el.textContent.trim().toLowerCase();
                    return text === 'restart' || text === '重启' || text.includes('restart');
                });
                if (target) {
                    target.click();
                    return true;
                }
                const powerBtn = document.querySelector('button[class*="power"], button[class*="restart"]');
                if (powerBtn) {
                    powerBtn.click();
                    return true;
                }
                return false;
                """
                try:
                    res = sb.execute_script(js_click_script)
                    if res:
                        log("✅ 成功通过 JS 绕过 DOM 限制强行触发了 Restart 点击！")
                        btn_clicked = True
                    else:
                        log("❌ JS 引擎在当前页面中也未能定位到任何符合条件的 'Restart' 元素")
                except Exception as js_err:
                    log(f"❌ 执行高阶 JS 强打失败: {js_err}")

            if btn_clicked:
                log("🚀 重启指令已成功发送。")
                sb.sleep(3)
            else:
                raise Exception("❌ 页面上未找到可点击的 Start / Restart 按钮")

        except Exception as e:
            error_msg = f"❌ 脚本运行出错: \n {str(e)}"
            log(error_msg)
        finally:
            log("🏁 脚本执行完毕.")
            # 汇总所有日志发送至 Telegram
            full_notification_text = "\n".join(msg_logs)
            send_tg_notification(f"<b>Therose 续期与重启报告</b>\n\n{full_notification_text}")

if __name__ == "__main__":
    run_automation()
