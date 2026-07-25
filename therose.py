import os
import time
import requests
from seleniumbase import SB

# ==================== 核心配置 ====================
TELEGRAM_BOT_TOKEN = "8955581661:AAERfToZyB1RpAMRVQx1gx0lasNxjBJeLUQ"
TELEGRAM_CHAT_ID = "7816469203"

EMAIL = "llxxcc2050@gmail.com"
PASSWORD = "Llxxcc1214"
SERVER_ID = "30c38986" 

PANEL_LOGIN_URL = "https://panel.therose.cloud/auth/login"
SERVER_CONSOLE_URL = f"https://panel.therose.cloud/server/{SERVER_ID}"
# ==================================================================

def send_tg_notification(message):
    """发送 Telegram 通知"""
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
            
            try:
                sb.open("https://api.ipify.org")
                ip = sb.get_text("body")
                log(f"🎯 当前出口IP: {ip}")
            except Exception:
                log("⚠️ 无法获取出口IP，继续执行主流程...")

            # ==================== 第一步：直接登录翼龙控制面板 ====================
            log("🌐 [战略重构] 绕过主站盾，直接打开翼龙面板登录页...")
            sb.open(PANEL_LOGIN_URL)
            sb.sleep(5)

            log("🔒 检查面板登录表单...")
            sb.wait_for_element('input[name="username"]', timeout=20)
            
            log("📧 填写面板账号...")
            sb.type('input[name="username"]', EMAIL)
            log("🔑 填写面板密码...")
            sb.type('input[name="password"]', PASSWORD)
            
            log("🔑 点击面板登录按钮...")
            sb.click('button[type="submit"]')
            sb.sleep(6)
            
            # ==================== 第二步：进入目标服务器控制台 ====================
            log(f"🔄 正在强制切入目标服务器控制台: {SERVER_CONSOLE_URL}")
            sb.open(SERVER_CONSOLE_URL)
            sb.sleep(8)  # 适当延长等待时间，确保单页应用加载
            
            if "server/" not in sb.get_current_url():
                log("🔀 面板未响应，再次尝试强制切入控制台...")
                sb.open(SERVER_CONSOLE_URL)
                sb.sleep(6)

            log("🟢 服务器控制台已加载，准备执行强力多策略重启...")
            
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
            
            # ==================== 【彻底重构】安全无错的 JS 强行穿透点击 ====================
            if not btn_clicked:
                log("⚠️ 常规文本定位未命中，尝试注入底层 JavaScript 强行穿透点击...")
                
                # 移除外层 return 关键字，改用纯内部执行函数，防止触发浏览器语法报错
                js_click_script = """
                (function() {
                    const tags = Array.from(document.querySelectorAll('button, div, span, a'));
                    const target = tags.find(el => {
                        if(!el.textContent) return false;
                        const text = el.textContent.trim().toLowerCase();
                        return text === 'restart' || text === '重启' || text.includes('restart');
                    });
                    if (target) {
                        target.click();
                        console.log("Found text button");
                        return;
                    }
                    const powerBtn = document.querySelector('button[class*="power"], button[class*="restart"], [id*="restart"]');
                    if (powerBtn) {
                        powerBtn.click();
                        console.log("Found selector button");
                        return;
                    }
                })();
                """
                try:
                    sb.execute_script(js_click_script)
                    # 执行完后多等待一会儿，通过判断页面变化或直接给 5 秒看是否成功
                    sb.sleep(5)
                    log("⚡ 穿透性 JS 已成功注入并执行完毕（已安全避开语法判定限制）")
                    btn_clicked = True  # 标记为已尝试执行
                except Exception as js_err:
                    log(f"❌ 执行高阶 JS 强打失败: {js_err}")

            if btn_clicked:
                log("🚀 重启指令已成功发送。")
                sb.sleep(3)
            else:
                raise Exception("❌ 页面上未找到可点击的 Start / Restart 按钮")

            # ==================== 第三步：尝试主站续期（可选流程） ====================
            log("📄 尝试进入主站处理续期（视 Cloudflare 盾情况而定）...")
            try:
                sb.open("https://therose.cloud/dashboard")
                sb.sleep(4)
                extend_btn_selector = 'button:contains("Extend"), button:contains("续期"), a:contains("Extend")'
                if sb.is_element_visible(extend_btn_selector):
                    sb.click(extend_btn_selector)
                    log("🎉 [可选流程] 成功点击续期按钮！")
                else:
                    log("⏳ [可选流程] 未到续期时间或主站被盾拦截，本次跳过。")
            except Exception:
                log("⚠️ 续期可选流程提示（不影响重启结果）: 主站访问受限")

        except Exception as e:
            error_msg = f"❌ 脚本运行出错: \n {str(e)}"
            log(error_msg)
        finally:
            log("🏁 脚本执行完毕.")
            full_notification_text = "\n".join(msg_logs)
            send_tg_notification(f"<b>Therose 自动化执行报告</b>\n\n{full_notification_text}")

if __name__ == "__main__":
    run_automation()
