"""
================================================================================
  PAYOMBOYZ TOKEN FINDER COG & AUTOQUEST BRIDGE
  Unified Token Extractor integrated directly with พยอมบอยหมูสับจัดให้ (Container 1)
  Provides:
    - 🔐 Direct Login with Genuine Desktop Super Properties & Captcha Protection
    - 📷 Discord Remote Auth QR Code Scanner (Fixed HTTP 400 Ticket Exchange)
    - 💻 PC Automated Web Bridge (/token) & 1-line Console Helper
    - 📱 Mobile Web & Bookmarklet Helper
    - 🚀 1-Click "Send Token to Auto Quest" Instant Execution
    - 🛡️ Zero Retention Architecture: RAM-only, ephemeral views, 5-min auto-destruction
================================================================================
"""

import os
import sys
import io
import time
import json
import base64
import hashlib
import asyncio
import inspect
from typing import Optional, Dict, Any, List

import aiohttp
try:
    from curl_cffi.requests import AsyncSession as CurlAsyncSession
    HAVE_CURL_CFFI = True
except ImportError:
    HAVE_CURL_CFFI = False
import discord
from discord.ext import commands
from discord import app_commands, ui
import qrcode
import websockets
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

try:
    from bot.captcha_solver import solve_discord_hcaptcha
except ImportError:
    try:
        from captcha_solver import solve_discord_hcaptcha
    except ImportError:
        async def solve_discord_hcaptcha(*args, **kwargs):
            return None

# Ensure DiscordAutoquest2 is accessible
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUTOQUEST2_DIR = os.path.join(_BASE_DIR, "DiscordAutoquest2")
if os.path.exists(_AUTOQUEST2_DIR) and _AUTOQUEST2_DIR not in sys.path:
    sys.path.insert(0, _AUTOQUEST2_DIR)

try:
    from payomboyz_autoquest import (
        state,
        worker_pool,
        DiscordQuestV10Handler,
        UserQuestJob,
        VisualEmbedEngine,
        build_quest_selection_embed,
        QuestSelectionView
    )
except ImportError:
    # Graceful fallback if imported in standalone context
    state = None
    worker_pool = None
    DiscordQuestV10Handler = None
    UserQuestJob = None
    VisualEmbedEngine = None
    build_quest_selection_embed = None
    QuestSelectionView = None

COLOR_PRIMARY = 0x5865F2    # Blurple
COLOR_SUCCESS = 0x57F287    # Green
COLOR_WARNING = 0xFEE75C    # Gold
COLOR_DANGER = 0xED4245     # Red
COLOR_EXPIRED = 0x2B2D31    # Dark Slate

TOKEN_BRIDGE_URL = os.getenv("TOKEN_BRIDGE_URL", "https://payomboyz-aihub.onrender.com/token")


def _log_live_interaction(line: str):
    if os.name == "nt" and os.path.isdir(r"D:\Deobfuscate"):
        try:
            with open(r"D:\Deobfuscate\live_interaction.log", "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

# Genuine Discord Web Client Super Properties & Live Build Number
DISCORD_CLIENT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

DISCORD_CLIENT_SUPER_PROPERTIES = {
    "os": "Windows",
    "browser": "Chrome",
    "device": "",
    "system_locale": "th-TH",
    "browser_user_agent": DISCORD_CLIENT_UA,
    "browser_version": "128.0.0.0",
    "os_version": "10",
    "referrer": "",
    "referring_domain": "",
    "referrer_current": "",
    "referring_domain_current": "",
    "release_channel": "stable",
    "client_build_number": 643186,
    "client_event_source": None
}
ENCODED_SUPER_PROPERTIES = base64.b64encode(
    json.dumps(DISCORD_CLIENT_SUPER_PROPERTIES).encode("utf-8")
).decode("utf-8")


# ─────────────────────────────────────────────────────────────
# 1. 1-CLICK ACTION BRIDGE: SEND TOKEN DIRECTLY TO AUTOQUEST
# ─────────────────────────────────────────────────────────────
async def enqueue_token_for_autoquest(interaction: discord.Interaction, token: str):
    """Feeds a retrieved token directly into AutoQuest worker pool without manual copy-paste."""
    guild = interaction.guild
    if not guild:
        return await interaction.followup.send("⚠️ กรุณาใช้งานฟังก์ชันนี้ภายในเซิร์ฟเวอร์", ephemeral=True)

    if not worker_pool or not state or not DiscordQuestV10Handler:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "token": token,
                    "guild_id": str(guild.id),
                    "user_id": str(interaction.user.id),
                    "status_channel_id": str(interaction.channel_id),
                    "result_channel_id": str(interaction.channel_id)
                }
                async with session.post(
                    "http://127.0.0.1:5050/api/start_quest",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status_url = data.get("status_url") or f"https://discord.com/channels/{guild.id}/{interaction.channel_id}"
                        check_view = discord.ui.View()
                        check_view.add_item(discord.ui.Button(
                            label="🔍 CHECK STATUS",
                            style=discord.ButtonStyle.link,
                            url=status_url
                        ))
                        username = data.get("username", "User")
                        return await interaction.followup.send(
                            content=(
                                f"🚀 **ส่ง Token เข้าสู่ระบบ Auto Quest เรียบร้อยแล้ว!**\n"
                                f"👤 **บัญชี Discord:** `{username}`\n"
                                f"📍 **ห้องสถานะสด:** <#{interaction.channel_id}>\n"
                                f"👉 คลิกปุ่ม **[🔍 CHECK STATUS]** ด้านล่างเพื่อติดตามการทำเควสแบบเรียลไทม์ได้ทันที"
                            ),
                            view=check_view,
                            ephemeral=True
                        )
                    else:
                        try:
                            err_data = await resp.json()
                            err_msg = err_data.get("error", "ไม่สามารถส่ง Token ได้")
                        except Exception:
                            err_msg = f"HTTP {resp.status}"
                        return await interaction.followup.send(
                            f"❌ **AutoQuest แจ้งเตือน:** {err_msg}",
                            ephemeral=True
                        )
        except Exception as bridge_err:
            print(f"[BridgeError] AutoQuest bridge to port 5050 failed: {bridge_err}", flush=True)
            return await interaction.followup.send(
                "⚠️ ระบบ Auto Quest Engine ยังไม่พร้อมทำงาน กรุณาคัดลอก Token ไปวางด้วยตนเอง หรือใช้คำสั่ง `/quest start`",
                ephemeral=True
            )

    # 1. Validate token & fetch profile
    profile = await DiscordQuestV10Handler.validate_token(token)
    if not profile:
        return await interaction.followup.send(
            "❌ **Token ไม่ถูกต้อง หรือหมดอายุแล้ว!** กรุณาลองดึงใหม่อีกครั้ง",
            ephemeral=True
        )

    # 2. Check quota & VIP status
    is_pro = state.is_user_pro(interaction.user.id, interaction.user, guild.id)
    can_proceed, count = state.check_and_increment_quota(interaction.user.id, is_pro)
    if not can_proceed:
        return await interaction.followup.send(
            "⚠️ **คุณใช้โควตาทำเควสฟรีครบ 3 ครั้งสำหรับวันนี้แล้ว!**\n"
            "💎 อัปเกรดเป็น **VIP Quest** หรือใช้คำสั่ง `/quest redeem` เพื่อรับโควตาไม่จำกัด",
            ephemeral=True
        )

    # 3. Resolve status & result channels safely
    cfg = state.get_guild(guild.id)
    status_ch_id = cfg.get("status_channel_id")
    result_ch_id = cfg.get("result_channel_id")

    status_ch = None
    if status_ch_id:
        status_ch = guild.get_channel(status_ch_id)
        if not status_ch:
            try:
                status_ch = await guild.fetch_channel(status_ch_id)
            except Exception:
                pass
    if not status_ch or not hasattr(status_ch, "send"):
        status_ch = interaction.channel

    result_ch = None
    if result_ch_id:
        result_ch = guild.get_channel(result_ch_id)
        if not result_ch:
            try:
                result_ch = await guild.fetch_channel(result_ch_id)
            except Exception:
                pass
    if not result_ch or not hasattr(result_ch, "send"):
        result_ch = interaction.channel

    # 4. Interactive Quest Selection (DevilQuest Parity)
    if build_quest_selection_embed and QuestSelectionView:
        quest_data = await DiscordQuestV10Handler.fetch_quests(token)
        raw_quests = quest_data.get("quests", [])

        active_quests = []
        now_utc = datetime.now(timezone.utc)
        for q in raw_quests:
            cfg_q = q.get("config", {})
            exp_str = cfg_q.get("expires_at")
            if exp_str:
                try:
                    exp_dt = datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
                    if exp_dt <= now_utc:
                        continue
                except Exception:
                    pass
            user_status = q.get("user_status") or {}
            if not user_status.get("completed_at") or not user_status.get("claimed_at"):
                active_quests.append(q)

        if not active_quests:
            return await interaction.followup.send(
                "🎉 **บัญชี Discord ของคุณไม่มีเควสค้าง หรือทำเควสทั้งหมดและรับรางวัลครบแล้ว!**",
                ephemeral=True
            )

        video_count = 0
        game_count = 0
        quest_info_list = []
        for idx, q in enumerate(active_quests, start=1):
            q_id = str(q.get("id"))
            cfg_q = q.get("config", {})
            msgs = cfg_q.get("messages", {})
            q_name = msgs.get("quest_name") or msgs.get("game_title") or q.get("name") or f"Quest {q_id}"

            tasks = None
            if cfg_q.get("task_config_v2", {}).get("tasks"):
                tasks = cfg_q["task_config_v2"]["tasks"]
            elif cfg_q.get("task_config", {}).get("tasks"):
                tasks = cfg_q["task_config"]["tasks"]
            else:
                for k in q:
                    if isinstance(q[k], dict) and q[k].get("tasks"):
                        tasks = q[k]["tasks"]
                        break
            tasks = tasks or {}
            is_vid = any(t in tasks for t in ('WATCH_VIDEO', 'WATCH_VIDEO_ON_MOBILE'))
            if is_vid:
                video_count += 1
                q_type = "video"
            else:
                game_count += 1
                q_type = "game"

            quest_info_list.append({
                "index": idx,
                "id": q_id,
                "name": q_name,
                "type": q_type,
                "quest": q
            })

        embed = build_quest_selection_embed(
            user=interaction.user,
            profile=profile,
            quest_info_list=quest_info_list,
            video_count=video_count,
            game_count=game_count,
            is_pro=is_pro
        )
        view = QuestSelectionView(
            user=interaction.user,
            tokens=[token],
            profile=profile,
            active_quests=active_quests,
            quest_info_list=quest_info_list,
            status_channel=status_ch,
            result_channel=result_ch,
            guild=guild,
            is_pro=is_pro
        )
        return await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # Fallback if UI components are not available
    job = UserQuestJob(
        guild=guild,
        user=interaction.user,
        profile=profile,
        tokens=[token],
        status_channel=status_ch,
        result_channel=result_ch
    )
    await worker_pool.enqueue(job)

    # 5. Build confirmation embed & jump link
    status_url = f"https://discord.com/channels/{guild.id}/{status_ch.id}"
    check_view = discord.ui.View()
    check_view.add_item(discord.ui.Button(
        label="🔍 CHECK STATUS",
        style=discord.ButtonStyle.link,
        url=status_url
    ))

    quota_msg = "💎 สิทธิ์การใช้งาน: **PRO (ไม่จำกัดโควตา)**" if is_pro else f"📊 โควตาวันนี้: **{count}/3 ครั้ง**"
    username = profile.get("username", "User")
    await interaction.followup.send(
        content=(
            f"🚀 **ส่ง Token เข้าสู่ระบบ Auto Quest เรียบร้อยแล้ว!**\n"
            f"👤 **บัญชี Discord:** `{username}`\n"
            f"📍 **ห้องสถานะสด:** {status_ch.mention}\n"
            f"🏆 **ห้องผลลัพธ์ของรางวัล:** {result_ch.mention}\n"
            f"{quota_msg}\n"
            f"👉 คลิกปุ่ม **[🔍 CHECK STATUS]** ด้านล่างเพื่อติดตามการทำเควสแบบเรียลไทม์ได้ทันที"
        ),
        view=check_view,
        ephemeral=True
    )


# ─────────────────────────────────────────────────────────────
# 2. SUCCESS VIEW WITH 1-CLICK AUTOQUEST BUTTON
# ─────────────────────────────────────────────────────────────
class TokenResultSuccessView(discord.ui.View):
    """Attached to successful token extraction responses."""
    def __init__(self, token: str, user_id: int):
        super().__init__(timeout=300)
        self.token = token
        self.user_id = user_id
        self.add_item(discord.ui.Button(
            label="🌐 เปิด Discord Web",
            style=discord.ButtonStyle.link,
            url="https://discord.com/app"
        ))

    @discord.ui.button(
        label="🚀 ส่ง Token ไปทำ Auto Quest ทันที",
        style=discord.ButtonStyle.success,
        emoji="⚡",
        custom_id="pbg_token:btn_send_autoquest",
        row=0
    )
    async def btn_send_quest(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ ข้อความนี้เป็นของผู้อื่น", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        button.disabled = True
        button.label = "กำลังรัน Auto Quest..."
        try:
            await interaction.edit_original_response(view=self)
        except Exception:
            pass
        await enqueue_token_for_autoquest(interaction, self.token)

    @discord.ui.button(
        label="🗑️ ทำลายข้อความทันที",
        style=discord.ButtonStyle.danger,
        custom_id="pbg_token:btn_destroy_success",
        row=0
    )
    async def btn_destroy(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ ข้อความนี้เป็นของผู้อื่น", ephemeral=True)
        expired_embed = discord.Embed(
            title="🔒 ทำลายข้อความเรียบร้อยแล้ว",
            description="ข้อความคำแนะนำและข้อมูล Token ถูกปิดการใช้งานและล้างออกจากระบบเพื่อความปลอดภัยเรียบร้อยแล้ว",
            color=COLOR_EXPIRED
        )
        await interaction.response.edit_message(embed=expired_embed, view=None, attachments=[])


class EphemeralActionToolbar(discord.ui.View):
    """General toolbar for instruction/info pages with destroy button."""
    def __init__(self, user_id: int, web_url: Optional[str] = None):
        super().__init__(timeout=300)
        self.user_id = user_id
        if web_url:
            self.add_item(discord.ui.Button(
                label="🌐 เปิดเว็บดึง Token อัตโนมัติ",
                style=discord.ButtonStyle.link,
                url=web_url
            ))
        self.add_item(discord.ui.Button(
            label="🌐 เปิด Discord Web",
            style=discord.ButtonStyle.link,
            url="https://discord.com/app"
        ))

    @discord.ui.button(
        label="🗑️ ทำลายข้อความทันที",
        style=discord.ButtonStyle.danger,
        custom_id="pbg_token:btn_destroy_toolbar"
    )
    async def btn_destroy(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ ข้อความนี้เป็นของผู้อื่น", ephemeral=True)
        expired_embed = discord.Embed(
            title="🔒 ทำลายข้อความเรียบร้อยแล้ว",
            description="ข้อความคำแนะนำถูกปิดการใช้งานและทำลายเพื่อความปลอดภัยเรียบร้อยแล้ว",
            color=COLOR_EXPIRED
        )
        await interaction.response.edit_message(embed=expired_embed, view=None, attachments=[])


# ─────────────────────────────────────────────────────────────
# 3. DIRECT LOGIN TOKEN EXTRACTOR MODAL (DESKTOP EMULATION)
# ─────────────────────────────────────────────────────────────
class TokenLoginExtractorModal(discord.ui.Modal, title="🔐 ล็อกอินดึง Token อัตโนมัติ (ไม่ต้อง F12)"):
    email = discord.ui.TextInput(
        label="อีเมล Discord หรือ เบอร์โทรศัพท์",
        placeholder="example@email.com หรือ เบอร์โทรศัพท์...",
        required=True
    )
    password = discord.ui.TextInput(
        label="รหัสผ่านบัญชี Discord",
        placeholder="รหัสผ่านบัญชี Discord ของคุณ...",
        style=discord.TextStyle.short,
        required=True
    )
    mfa_code = discord.ui.TextInput(
        label="รหัส 2FA Authenticator 6 หลัก (ถ้ามี)",
        placeholder="ใส่รหัส Authenticator 6 หลัก หรือเว้นว่างได้",
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        _log_live_interaction(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Modal submitted by {interaction.user} (ID: {interaction.user.id}) email={self.email.value[:4]}***")
        await interaction.response.defer(ephemeral=True, thinking=True)
        login_val = self.email.value.strip()
        pass_val = self.password.value.strip()
        mfa_val = self.mfa_code.value.strip()

        payload = {
            "login": login_val,
            "password": pass_val,
            "undelete": False,
            "captcha_key": None,
            "login_source": None,
            "gift_code_sku_id": None,
            "login_status": None
        }

        # Authentic Desktop Client Headers with Super Properties
        headers = {
            "Content-Type": "application/json",
            "User-Agent": DISCORD_CLIENT_UA,
            "Referer": "https://discord.com/login",
            "Origin": "https://discord.com",
            "X-Super-Properties": ENCODED_SUPER_PROPERTIES,
            "X-Discord-Locale": "th",
            "X-Discord-Timezone": "Asia/Bangkok",
            "X-Debug-Options": "bugReporterEnabled"
        }

        token = None
        error_msg = None
        hit_captcha = False

        # ─── STRATEGY 0: Local Stealth Browser Auth (runs on this residential machine) ───
        # Discord always challenges captcha against server/cloud IPs from raw API.
        # Stealth browser on local IP bypasses this entirely via real browser session.
        try:
            from bot.local_stealth_auth import login_and_extract_token as _stealth_login
            print(f"[DirectAuth] Trying Local Stealth Browser Auth for {login_val[:3]}***", flush=True)
            stealth_result = await _stealth_login(login_val, pass_val, mfa_val or None, timeout=40)
            if stealth_result.get("success") and stealth_result.get("token"):
                token = stealth_result["token"]
                print(f"[DirectAuth] Stealth Auth SUCCESS! Token length={len(token)}", flush=True)
            elif stealth_result.get("mfa_required"):
                # MFA required — fall through to handle ticket exchange
                print(f"[DirectAuth] Stealth Auth: MFA required", flush=True)
                error_msg = "🔐 บัญชีของคุณเปิดใช้งาน 2FA กรุณากรอกรหัส Authenticator 6 หลักในช่อง 2FA ด้วยครับ"
            elif stealth_result.get("error"):
                err = stealth_result["error"]
                print(f"[DirectAuth] Stealth Auth error: {err}", flush=True)
                # If it's a credentials error, show it directly
                if "ไม่ถูกต้อง" in err or "wrong" in err.lower() or "invalid" in err.lower():
                    error_msg = f"🔑 {err}"
                # else fall through to raw API as last resort
        except Exception as _stealth_ex:
            print(f"[DirectAuth] Stealth Auth module exception: {_stealth_ex}", flush=True)

        if token or error_msg:
            # Stealth auth gave us a conclusive result — skip raw API
            data = {"token": token} if token else {}
            resp_status = 200 if token else 400

        # ─── STRATEGY 1: Raw API via curl_cffi (Chrome TLS fingerprint) ───
        # Note: This path will typically get a captcha challenge from server IP.
        # It is kept as a last resort in case stealth auth fails to import.
        if (not token and not error_msg) and HAVE_CURL_CFFI:
            try:
                async with CurlAsyncSession(impersonate="chrome124") as curl_s:
                    await curl_s.get("https://discord.com/login", headers={"User-Agent": DISCORD_CLIENT_UA}, timeout=8)
                    r_exp = await curl_s.get(
                        "https://discord.com/api/v9/experiments",
                        headers={"User-Agent": DISCORD_CLIENT_UA, "X-Super-Properties": ENCODED_SUPER_PROPERTIES},
                        timeout=8
                    )
                    if r_exp.status_code == 200:
                        try:
                            fp_val = r_exp.json().get("fingerprint")
                            if fp_val:
                                headers["X-Fingerprint"] = fp_val
                        except Exception:
                            pass

                    curl_resp = await curl_s.post(
                        "https://discord.com/api/v9/auth/login",
                        json=payload,
                        headers=headers,
                        timeout=15
                    )
                    resp_status = curl_resp.status_code
                    try:
                        data = curl_resp.json()
                    except Exception:
                        data = {}
                    used_curl = True

                    if resp_status == 400 and ("captcha_key" in data or "captcha_sitekey" in data):
                        sitekey = data.get("captcha_sitekey", "4c672d35-0701-42b2-88c3-78380b0db560")
                        rqdata = data.get("captcha_rqdata")
                        rqtoken = data.get("captcha_rqtoken")
                        print(f"[DirectAuth] Discord requested captcha (sitekey={sitekey}). Invoking Local Stealth Engine...", flush=True)

                        try:
                            from bot.local_stealth_auth import login_and_extract_token
                            stealth_res = await login_and_extract_token(login_val, pass_val, mfa_val)
                            if stealth_res.get("success") and stealth_res.get("token"):
                                token = stealth_res["token"]
                                resp_status = 200
                                data = {"token": token}
                                print(f"[DirectAuth] 🎯 Local Stealth Engine extracted token successfully!", flush=True)
                            elif stealth_res.get("mfa_required"):
                                data["mfa"] = True
                                data["ticket"] = stealth_res.get("ticket")
                            elif stealth_res.get("error"):
                                error_msg = stealth_res.get("error")
                        except Exception as se:
                            print(f"[DirectAuth] Local stealth auth exception: {se}", flush=True)

                        if not token:
                            solved_key = await solve_discord_hcaptcha(sitekey=sitekey, rqdata=rqdata, rqtoken=rqtoken)
                            if solved_key:
                                print(f"[DirectAuth] Auto-Solver successfully generated token! Resubmitting login...", flush=True)
                                payload["captcha_key"] = solved_key
                                if rqtoken:
                                    payload["captcha_rqtoken"] = rqtoken
                                headers["X-Captcha-Key"] = solved_key
                                if rqtoken:
                                    headers["X-Captcha-Rqtoken"] = rqtoken

                                resubmit_resp = await curl_s.post(
                                    "https://discord.com/api/v9/auth/login",
                                    json=payload,
                                    headers=headers,
                                    timeout=15
                                )
                                resp_status = resubmit_resp.status_code
                                try:
                                    data = resubmit_resp.json()
                                except Exception:
                                    data = {}
            except Exception as ce:
                print(f"[DirectAuth] curl_cffi attempt failed: {ce}", flush=True)

        if not used_curl or resp_status == 0:
            try:
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(
                            "https://discord.com/api/v9/experiments",
                            headers={"User-Agent": DISCORD_CLIENT_UA, "X-Super-Properties": ENCODED_SUPER_PROPERTIES},
                            timeout=aiohttp.ClientTimeout(total=8)
                        ) as r_exp:
                            if r_exp.status == 200:
                                exp_json = await r_exp.json()
                                if exp_json.get("fingerprint"):
                                    headers["X-Fingerprint"] = exp_json["fingerprint"]
                    except Exception:
                        pass

                    async with session.post(
                        "https://discord.com/api/v9/auth/login",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=15)
                    ) as resp:
                        resp_status = resp.status
                        data = await resp.json()

                    if resp_status == 400 and ("captcha_key" in data or "captcha_sitekey" in data):
                        sitekey = data.get("captcha_sitekey", "4c672d35-0701-42b2-88c3-78380b0db560")
                        rqdata = data.get("captcha_rqdata")
                        rqtoken = data.get("captcha_rqtoken")
                        print(f"[DirectAuth aiohttp] Discord requested captcha. Invoking Local Stealth Engine...", flush=True)

                        try:
                            from bot.local_stealth_auth import login_and_extract_token
                            stealth_res = await login_and_extract_token(login_val, pass_val, mfa_val)
                            if stealth_res.get("success") and stealth_res.get("token"):
                                token = stealth_res["token"]
                                resp_status = 200
                                data = {"token": token}
                                print(f"[DirectAuth aiohttp] 🎯 Local Stealth Engine extracted token successfully!", flush=True)
                            elif stealth_res.get("mfa_required"):
                                data["mfa"] = True
                                data["ticket"] = stealth_res.get("ticket")
                            elif stealth_res.get("error"):
                                error_msg = stealth_res.get("error")
                        except Exception as se:
                            print(f"[DirectAuth aiohttp] Local stealth auth exception: {se}", flush=True)

                        if not token:
                            solved_key = await solve_discord_hcaptcha(sitekey=sitekey, rqdata=rqdata, rqtoken=rqtoken)
                            if solved_key:
                                payload["captcha_key"] = solved_key
                                if rqtoken:
                                    payload["captcha_rqtoken"] = rqtoken
                                headers["X-Captcha-Key"] = solved_key
                                if rqtoken:
                                    headers["X-Captcha-Rqtoken"] = rqtoken

                                async with session.post(
                                    "https://discord.com/api/v9/auth/login",
                                    json=payload,
                                    headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=15)
                                ) as resubmit_resp:
                                    resp_status = resubmit_resp.status
                                    data = await resubmit_resp.json()
            except Exception as e:
                error_msg = f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ Discord Auth: {e}"

        try:
            if resp_status == 200 and "token" in data:
                token = data["token"]
            elif data.get("mfa") and data.get("ticket"):
                ticket = data["ticket"]
                if mfa_val:
                    mfa_payload = {
                        "code": mfa_val,
                        "ticket": ticket,
                        "login_source": None,
                        "gift_code_sku_id": None
                    }
                    if HAVE_CURL_CFFI:
                        async with CurlAsyncSession(impersonate="chrome124") as curl_s:
                            mfa_resp = await curl_s.post(
                                "https://discord.com/api/v9/auth/mfa/totp",
                                json=mfa_payload,
                                headers=headers,
                                timeout=15
                            )
                            mfa_data = mfa_resp.json()
                            if mfa_resp.status_code == 200 and "token" in mfa_data:
                                token = mfa_data["token"]
                            else:
                                error_msg = "❌ รหัส 2FA (Authenticator) ไม่ถูกต้อง หรือหมดอายุแล้ว"
                    else:
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                "https://discord.com/api/v9/auth/mfa/totp",
                                json=mfa_payload,
                                headers=headers,
                                timeout=aiohttp.ClientTimeout(total=15)
                            ) as mfa_resp:
                                mfa_data = await mfa_resp.json()
                                if mfa_resp.status == 200 and "token" in mfa_data:
                                    token = mfa_data["token"]
                                else:
                                    error_msg = "❌ รหัส 2FA (Authenticator) ไม่ถูกต้อง หรือหมดอายุแล้ว"
                else:
                    error_msg = "🔐 บัญชีของคุณเปิดใช้งาน 2FA กรุณากรอกรหัส Authenticator 6 หลักในช่อง 2FA ด้วยครับ"
            elif "password" in str(data).lower() or "login" in str(data).lower():
                error_msg = "🔑 อีเมลหรือรหัสผ่าน Discord ไม่ถูกต้อง กรุณาตรวจสอบข้อมูลและลองใหม่อีกครั้ง"
            elif "captcha_key" in data or "captcha_sitekey" in data:
                hit_captcha = True
                error_msg = (
                    "🧩 **Discord ร้องขอการยืนยันตัวตนเพิ่มเติม (Security Challenge)**\n\n"
                    "ระบบตรวจพบบัญชีนี้เปิดการป้องกันความปลอดภัยจากอุปกรณ์ใหม่\n"
                    "💡 **วิธีดึง Token ทันทีที่สะดวกและแม่นยำที่สุด:**\n"
                    "• **กดปุ่ม \"📷 สลับไปสแกน QR Code\" ด้านล่างนี้:** เปิด Discord บนโทรศัพท์มือถือ สแกนยืนยัน Token จะส่งกลับมาให้คุณทันที 100%!\n"
                    "• **หรือบน PC:** กดปุ่ม **[💻 สำหรับ PC (Console 5 วิ)]** บนแผงหลัก วางโค้ด 1 บรรทัด ได้ Token ทันที"
                )
            elif not token and not error_msg:
                error_msg = f"❌ ไม่สามารถล็อกอินได้: {data.get('message', 'โปรดลองใช้วิธีสแกน QR Code แทน')}"
        except Exception as e:
            if not error_msg:
                error_msg = f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ Discord Auth: {e}"

        if token:
            now_ts = int(time.time())
            expire_ts = now_ts + 300
            embed = discord.Embed(
                title="✅ ล็อกอินดึง Token สำเร็จ 100%!",
                description=(
                    f"👤 **ผู้ใช้งาน:** {interaction.user.mention}\n\n"
                    "🔑 **User Token ของคุณ (แตะเพื่อคัดลอก):**\n"
                    f"```\n{token}\n```\n"
                    "🚀 **ทำเควสทันที:** คุณสามารถกดปุ่มสีเขียว **[🚀 ส่ง Token ไปทำ Auto Quest ทันที]** ด้านล่างได้เลย บอทจะเริ่มทำเควสให้ทันทีโดยไม่ต้องก็อปปี้!\n\n"
                    "🛡️ **ระบบรักษาความปลอดภัย (Zero Retention):**\n"
                    "• รหัสผ่านและ Token ไม่มีการบันทึกลง Database ข้อมูลประมวลผลใน RAM ชั่วคราวเท่านั้น\n"
                    f"• ข้อความนี้จะถูกทำลายและปิดการใช้งานภายใน 5 นาที (<t:{expire_ts}:R>)"
                ),
                color=COLOR_SUCCESS
            )
            embed.set_footer(text="PAYOMBØYZ SECURITY • Direct Auth Session (Local Residential Node)")
            view = TokenResultSuccessView(token=token, user_id=interaction.user.id)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        else:
            embed = discord.Embed(
                title="⚠️ ดึง Token ไม่สำเร็จ",
                description=error_msg,
                color=COLOR_DANGER
            )
            embed.set_footer(text="PAYOMBØYZ SECURITY • Local Residential Node")
            view = discord.ui.View()
            if hit_captcha:
                view.add_item(discord.ui.Button(
                    label="🌐 เปิดเว็บดึง Token (เน็ตบ้าน ไม่ติด Captcha 100%)",
                    style=discord.ButtonStyle.link,
                    url=TOKEN_BRIDGE_URL,
                    emoji="🌐"
                ))
                qr_btn = discord.ui.Button(
                    label="📷 สลับไปสแกน QR Code",
                    style=discord.ButtonStyle.primary,
                    emoji="📷",
                    custom_id="pbg_token:btn_fallback_qr"
                )
                async def fallback_qr_cb(btn_interaction: discord.Interaction):
                    await btn_interaction.response.defer(ephemeral=True, thinking=True)
                    worker = DiscordRemoteAuthWorker(btn_interaction)
                    asyncio.create_task(worker.execute())
                qr_btn.callback = fallback_qr_cb
                view.add_item(qr_btn)

            view.add_item(discord.ui.Button(
                label="🌐 เปิด Discord Web",
                style=discord.ButtonStyle.link,
                url="https://discord.com/app"
            ))
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# ─────────────────────────────────────────────────────────────
# 4. DISCORD REMOTE AUTH QR CODE WORKER (FIXED HTTP 400 ERROR)
# ─────────────────────────────────────────────────────────────
class DiscordRemoteAuthWorker:
    """
    Implements true Discord Remote Authentication WebSocket Protocol (v2).
    Generates QR code for mobile Discord app scanner, listens for user approval,
    decrypts the user token in memory, and delivers it to the user's ephemeral channel.
    Injects full Desktop Super Properties into ticket exchange to prevent HTTP 400.
    """
    GATEWAY_URL = "wss://remote-auth-gateway.discord.gg/?v=2"
    LOGIN_URL = "https://discord.com/api/v9/users/@me/remote-auth/login"

    def __init__(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        
        spki_der = self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.encoded_public_key = base64.b64encode(spki_der).decode("utf-8")
        self.fingerprint = None
        self.running = True

    def generate_qr_file(self, fingerprint: str) -> discord.File:
        qr_target = f"https://discord.com/ra/{fingerprint}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2
        )
        qr.add_data(qr_target)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1E1F22", back_color="#FFFFFF")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return discord.File(buf, filename="discord_qr.png")

    async def execute(self):
        try:
            # 1. Warm up session and fetch real Cloudflare & Discord cookies (__dcfduid, __sdcfduid)
            harvested_cookies = {}
            try:
                async with aiohttp.ClientSession() as prep_session:
                    async with prep_session.get(
                        "https://discord.com/login",
                        headers={"User-Agent": DISCORD_CLIENT_UA},
                        timeout=aiohttp.ClientTimeout(total=8)
                    ) as prep_resp:
                        for k, v in prep_resp.cookies.items():
                            harvested_cookies[k] = v.value
            except Exception:
                pass

            # Adapt to websockets 13+ (additional_headers) vs legacy (extra_headers)
            ws_kwargs = {"origin": "https://discord.com"}
            sig = inspect.signature(websockets.connect)
            if "additional_headers" in sig.parameters:
                ws_kwargs["additional_headers"] = {"User-Agent": DISCORD_CLIENT_UA}
                ws_kwargs["user_agent_header"] = DISCORD_CLIENT_UA
            else:
                ws_kwargs["extra_headers"] = {"User-Agent": DISCORD_CLIENT_UA}

            async with websockets.connect(
                self.GATEWAY_URL,
                **ws_kwargs
            ) as ws:
                heartbeat_task = None
                
                async for raw_message in ws:
                    if not self.running:
                        break
                    
                    data = json.loads(raw_message)
                    op = data.get("op")

                    if op == "hello":
                        interval = data.get("heartbeat_interval", 41250) / 1000.0
                        
                        async def heartbeat_loop():
                            try:
                                while self.running:
                                    await asyncio.sleep(interval)
                                    await ws.send(json.dumps({"op": "heartbeat"}))
                            except Exception:
                                pass
                                
                        heartbeat_task = asyncio.create_task(heartbeat_loop())
                        
                        # Send init with public key
                        await ws.send(json.dumps({
                            "op": "init",
                            "encoded_public_key": self.encoded_public_key
                        }))

                    elif op == "nonce_proof":
                        encrypted_nonce = base64.b64decode(data["encrypted_nonce"])
                        decrypted_nonce = self.private_key.decrypt(
                            encrypted_nonce,
                            padding.OAEP(
                                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                algorithm=hashes.SHA256(),
                                label=None
                            )
                        )
                        nonce_hash = hashlib.sha256(decrypted_nonce).digest()
                        proof = base64.urlsafe_b64encode(nonce_hash).decode("utf-8").rstrip("=")
                        
                        await ws.send(json.dumps({
                            "op": "nonce_proof",
                            "proof": proof
                        }))

                    elif op == "pending_remote_init":
                        self.fingerprint = data.get("fingerprint")
                        if not self.fingerprint:
                            continue
                            
                        qr_file = self.generate_qr_file(self.fingerprint)
                        now_ts = int(time.time())
                        expire_ts = now_ts + 120  # QR valid for 2 mins

                        embed = discord.Embed(
                            title="📷 สแกน QR Code เพื่อดึง Token (Discord Remote Auth)",
                            description=(
                                f"👤 **ผู้ใช้งาน:** {self.interaction.user.mention} (`{self.interaction.user.id}`)\n\n"
                                "📱 **ขั้นตอนการสแกนด้วยโทรศัพท์มือถือ (ง่ายและปลอดภัยที่สุด):**\n"
                                "1. เปิดแอป **Discord บนโทรศัพท์มือถือ** ของท่าน\n"
                                "2. แตะที่ **รูปโปรไฟล์มุมขวาล่าง** เพื่อเข้าหน้าต่าง **การตั้งค่า (Settings)**\n"
                                "3. เลื่อนลงมาเลือกหัวข้อ **\"สแกนคิวอาร์โค้ด (Scan QR Code)\"**\n"
                                "4. ใช้กล้องมือถือสแกนรูปภาพ QR Code ด้านล่างนี้\n"
                                "5. กดปุ่ม **\"ยืนยันการเข้าสู่ระบบ (Yes, log me in)\"** บนมือถือ\n\n"
                                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"⏳ **สถานะ:** กำลังรอการสแกนจากโทรศัพท์... (หมดอายุ <t:{expire_ts}:R>)\n"
                                "🔒 *ระบบจะถอดรหัสและส่ง Token ให้คุณทันทีหลังกดยืนยัน*"
                            ),
                            color=COLOR_PRIMARY
                        )
                        embed.set_image(url="attachment://discord_qr.png")
                        embed.set_footer(text="PAYOMBØYZ REMOTE AUTH • เข้ารหัส 2048-bit RSA ชั่วคราวใน RAM")

                        view = EphemeralActionToolbar(user_id=self.interaction.user.id)
                        try:
                            await self.interaction.edit_original_response(embed=embed, attachments=[qr_file], view=view)
                        except Exception:
                            await self.interaction.followup.send(embed=embed, file=qr_file, view=view, ephemeral=True)

                    elif op == "pending_ticket":
                        # User scanned QR on phone
                        encrypted_user = base64.b64decode(data.get("encrypted_user_payload", ""))
                        try:
                            user_payload = self.private_key.decrypt(
                                encrypted_user,
                                padding.OAEP(
                                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                    algorithm=hashes.SHA256(),
                                    label=None
                                )
                            ).decode("utf-8")
                            parts = user_payload.split(":")
                            u_id = parts[0] if len(parts) > 0 else "Unknown"
                            u_name = parts[3] if len(parts) > 3 else "Discord User"
                        except Exception:
                            u_id = "Detected"
                            u_name = "Discord User"

                        scanned_embed = discord.Embed(
                            title="📲 ตรวจพบการสแกนแล้ว! รอการยืนยันบนโทรศัพท์",
                            description=(
                                f"👤 **พบบัญชี:** `{u_name}` (ID: `{u_id}`)\n\n"
                                "⚠️ **โปรดกดปุ่ม \"ยืนยันการเข้าสู่ระบบ (Yes, log me in)\" บนโทรศัพท์ของท่านทันที**\n"
                                "ระบบกำลังรอรับ Token เพื่อส่งกลับมาให้ท่านในข้อความนี้...\n\n"
                                "⏱️ *กรุณากดยืนยันภายใน 30 วินาที*"
                            ),
                            color=COLOR_WARNING
                        )
                        scanned_embed.set_footer(text="PAYOMBØYZ REMOTE AUTH • กำลังรออนุมัติ")
                        try:
                            await self.interaction.edit_original_response(embed=scanned_embed, attachments=[])
                        except Exception:
                            pass

                    elif op == "pending_login":
                        ticket = data.get("ticket")
                        if not ticket:
                            continue

                        # Exchange ticket for encrypted token
                        login_headers = {
                            "Origin": "https://discord.com",
                            "Referer": "https://discord.com/login",
                            "Content-Type": "application/json",
                            "User-Agent": DISCORD_CLIENT_UA,
                            "Accept": "*/*",
                            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
                            "X-Super-Properties": ENCODED_SUPER_PROPERTIES,
                            "X-Discord-Locale": "th",
                            "X-Discord-Timezone": "Asia/Bangkok"
                        }

                        login_data = {}
                        resp_status = 0
                        err_text = ""

                        # Use clean session with harvested cookies
                        try:
                            async with aiohttp.ClientSession(cookies=harvested_cookies) as session:
                                async with session.post(
                                    self.LOGIN_URL,
                                    json={"ticket": ticket},
                                    headers=login_headers,
                                    timeout=aiohttp.ClientTimeout(total=15)
                                ) as resp:
                                    resp_status = resp.status
                                    try:
                                        login_data = await resp.json()
                                    except Exception:
                                        err_text = await resp.text()
                                    print(f"[RemoteAuth] Ticket exchange status={resp_status}, keys={list(login_data.keys()) if isinstance(login_data, dict) else 'non-dict'}", flush=True)

                                # If captcha was requested on ticket exchange
                                if resp_status == 400 and isinstance(login_data, dict) and ("captcha_key" in login_data or "captcha_sitekey" in login_data):
                                    sitekey = login_data.get("captcha_sitekey", "4c672d35-0701-42b2-88c3-78380b0db560")
                                    rqdata = login_data.get("captcha_rqdata")
                                    rqtoken = login_data.get("captcha_rqtoken")
                                    print(f"[RemoteAuth] Captcha requested on ticket exchange (sitekey={sitekey}). Solving...", flush=True)
                                    solved_cap = await solve_discord_hcaptcha(sitekey=sitekey, rqdata=rqdata, rqtoken=rqtoken)
                                    if solved_cap:
                                        cap_payload = {"ticket": ticket, "captcha_key": solved_cap}
                                        if rqtoken:
                                            cap_payload["captcha_rqtoken"] = rqtoken
                                        async with session.post(
                                            self.LOGIN_URL,
                                            json=cap_payload,
                                            headers=login_headers,
                                            timeout=aiohttp.ClientTimeout(total=15)
                                        ) as resubmit_resp:
                                            resp_status = resubmit_resp.status
                                            try:
                                                login_data = await resubmit_resp.json()
                                            except Exception:
                                                err_text = await resubmit_resp.text()
                        except Exception as ex:
                            print(f"[RemoteAuth] Exception during ticket exchange: {ex}", flush=True)
                            err_text = str(ex)

                        if resp_status == 200:
                            enc_token_b64 = login_data.get("encrypted_token")
                            if enc_token_b64:
                                dec_token = self.private_key.decrypt(
                                    base64.b64decode(enc_token_b64),
                                    padding.OAEP(
                                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                        algorithm=hashes.SHA256(),
                                        label=None
                                    )
                                ).decode("utf-8")

                                now_ts = int(time.time())
                                expire_ts = now_ts + 300

                                success_embed = discord.Embed(
                                    title="✅ ดึง User Token สำเร็จเรียบร้อยแล้ว!",
                                    description=(
                                        f"👤 **ผู้ใช้งาน:** {self.interaction.user.mention}\n\n"
                                        "🔑 **Discord User Token ของคุณ (แตะเพื่อคัดลอก):**\n"
                                        f"```\n{dec_token}\n```\n"
                                        "🚀 **ทำเควสทันที:** คลิกปุ่มสีเขียว **[🚀 ส่ง Token ไปทำ Auto Quest ทันที]** ด้านล่างได้เลย บอทจะเริ่มทำเควสให้ทันที!\n\n"
                                        "🛡️ **ระบบรักษาความปลอดภัย (Zero Retention):**\n"
                                        "• ข้อมูลประมวลผลใน RAM ชั่วคราวเท่านั้น ไม่มีการบันทึกลงดิสก์หรือฐานข้อมูล\n"
                                        f"• ข้อความนี้จะถูกทำลายและปิดการใช้งานภายใน 5 นาที (<t:{expire_ts}:R>)"
                                    ),
                                    color=COLOR_SUCCESS
                                )
                                success_embed.set_footer(text="PAYOMBØYZ SECURITY • 100% Client-Side Delivery")
                                view = TokenResultSuccessView(token=dec_token, user_id=self.interaction.user.id)
                                try:
                                    await self.interaction.edit_original_response(embed=success_embed, view=view, attachments=[])
                                except Exception:
                                    pass
                                
                                self._schedule_final_destruction(self.interaction)
                                self.running = False
                                break
                        else:
                            print(f"[RemoteAuth] Login exchange rejected ({resp_status}): {err_text}", flush=True)

                            web_token_url = TOKEN_BRIDGE_URL
                            if "captcha" in err_text.lower():
                                fail_embed = discord.Embed(
                                    title="🛡️ Discord บังคับยืนยัน Captcha สำหรับ IP นี้",
                                    description=(
                                        "⚠️ **Discord บังคับแก้ Captcha สำหรับการแลกเปลี่ยน Token บน Cloud Node (Datacenter IP)**\n\n"
                                        "✨ **วิธีดึง Token ไร้ Captcha 100% (ทำผ่านเน็ตบ้านของคุณ):**\n"
                                        "• **บนคอม (PC):** คลิกปุ่มสีฟ้า **[🌐 เปิดเว็บ PAYOMBØYZ TOKEN]** ด้านล่างนี้เพื่อดึง Token บนเบราว์เซอร์ของคุณโดยตรง\n"
                                        "• **บนมือถือ:** เปิด Discord Web ใน Safari / Chrome แล้วแตะ Bookmarklet\n\n"
                                        "🚀 **เมื่อได้ Token แล้ว:** นำมาส่งในช่องบอท Auto Quest เพื่อเริ่มทำเควสได้ทันที!"
                                    ),
                                    color=COLOR_WARNING
                                )
                                fail_view = EphemeralActionToolbar(user_id=self.interaction.user.id, web_url=web_token_url)
                            else:
                                fail_embed = discord.Embed(
                                    title="❌ การยืนยันตัวตนล้มเหลว",
                                    description=(
                                        f"Discord ปฏิเสธการแลกเปลี่ยน Token (HTTP {resp_status}) หรือเซสชันหมดอายุ\n"
                                        "กรุณากดลองสแกนใหม่อีกครั้ง และตรวจสอบว่าโทรศัพท์เชื่อมต่ออินเทอร์เน็ตปกติ"
                                    ),
                                    color=COLOR_DANGER
                                )
                                fail_view = EphemeralActionToolbar(user_id=self.interaction.user.id, web_url=web_token_url)
                            try:
                                await self.interaction.edit_original_response(embed=fail_embed, attachments=[], view=fail_view)
                            except Exception:
                                pass
                            self.running = False
                            break

                    elif op == "cancel":
                        cancel_embed = discord.Embed(
                            title="❌ ยกเลิกการเข้าสู่ระบบ",
                            description="การเชื่อมต่อถูกยกเลิกจากโทรศัพท์ หรือหมดเวลาการเชื่อมต่อ กรุณากดปุ่มสร้าง QR Code ใหม่อีกครั้ง",
                            color=COLOR_DANGER
                        )
                        try:
                            await self.interaction.edit_original_response(embed=cancel_embed, attachments=[])
                        except Exception:
                            pass
                        self.running = False
                        break

                if heartbeat_task and not heartbeat_task.done():
                    heartbeat_task.cancel()

        except Exception as e:
            try:
                err_embed = discord.Embed(
                    title="⚠️ การเชื่อมต่อ QR Code สิ้นสุด",
                    description=f"เซสชันหมดเวลาหรือการเชื่อมต่อปิดลงแล้ว ({e})\nหากต้องการใช้งานโปรดกดปุ่มอีกครั้ง",
                    color=COLOR_EXPIRED
                )
                await self.interaction.edit_original_response(embed=err_embed, attachments=[])
            except Exception:
                pass

    def _schedule_final_destruction(self, interaction: discord.Interaction):
        async def expire():
            await asyncio.sleep(300)
            try:
                expired_embed = discord.Embed(
                    title="🔒 เซสชันแสดง Token หมดอายุแล้ว (5 นาที)",
                    description="ข้อความแสดง Token นี้ถูกทำลายและปิดการใช้งานเพื่อความปลอดภัยของคุณเรียบร้อยแล้ว",
                    color=COLOR_EXPIRED
                )
                await interaction.edit_original_response(embed=expired_embed, view=None, attachments=[])
            except Exception:
                pass
        asyncio.create_task(expire())


# ─────────────────────────────────────────────────────────────
# 5. MAIN PERSISTENT PANEL VIEW (/find_token)
# ─────────────────────────────────────────────────────────────
class FindTokenPanelView(discord.ui.View):
    """
    Persistent View for /find_token Panel.
    Equipped with real QR Code Login, PC Web Helper, Mobile Bookmarklet, and Direct Login.
    Survives bot restarts.
    """
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="🌐 เปิดเว็บดึง Token (เน็ตบ้าน ไม่ติด Captcha 100%)",
            style=discord.ButtonStyle.link,
            url=TOKEN_BRIDGE_URL,
            emoji="🌐",
            row=0
        ))

    # 🔐 ROW 0: BUTTON DIRECT LOGIN (ZERO F12)
    @discord.ui.button(
        label="ล็อกอินดึง Token (ไม่ต้อง F12)",
        style=discord.ButtonStyle.success,
        emoji="🔐",
        custom_id="pbg_find_token:btn_login",
        row=0
    )
    async def btn_login(self, interaction: discord.Interaction, button: discord.ui.Button):
        _log_live_interaction(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] btn_login clicked by {interaction.user} (ID: {interaction.user.id})")
        await interaction.response.send_modal(TokenLoginExtractorModal())

    # 📷 ROW 0: BUTTON REAL QR CODE LOGIN
    @discord.ui.button(
        label="สแกน QR Code (ดึง Token ออโต้)",
        style=discord.ButtonStyle.primary,
        emoji="📷",
        custom_id="pbg_find_token:btn_qr",
        row=0
    )
    async def btn_qr(self, interaction: discord.Interaction, button: discord.ui.Button):
        _log_live_interaction(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] btn_qr clicked by {interaction.user} (ID: {interaction.user.id})")
        await interaction.response.defer(ephemeral=True, thinking=True)
        worker = DiscordRemoteAuthWorker(interaction)
        asyncio.create_task(worker.execute())

    # 💻 ROW 1: BUTTON PC WEB & CONSOLE
    @discord.ui.button(
        label="สำหรับ PC (เปิดเว็บ / Console 5 วิ)",
        style=discord.ButtonStyle.secondary,
        emoji="💻",
        custom_id="pbg_find_token:btn_pc",
        row=1
    )
    async def btn_pc(self, interaction: discord.Interaction, button: discord.ui.Button):
        now_ts = int(time.time())
        expire_ts = now_ts + 300
        web_token_url = TOKEN_BRIDGE_URL

        embed = discord.Embed(
            title="💻 วิธีดึง Token บน PC / คอมพิวเตอร์ (ทำได้ใน 5 วินาที)",
            description=(
                f"👤 **ผู้ใช้งาน:** {interaction.user.mention} (`{interaction.user.id}`)\n\n"
                "🌟 **วิธีที่ 1: ดึงผ่าน Network Tab (F12) — แนะนำ! ง่ายสุด 100% ไม่ต้องวางโค้ด**\n"
                "1. เปิด Discord บนเบราว์เซอร์ (Chrome / Edge / Opera)\n"
                "2. กดปุ่ม **`Ctrl + Shift + I`** หรือปุ่ม **`F12`** เพื่อเปิด Developer Tools\n"
                "3. คลิกไปที่แท็บ **Network (เครือข่าย)** ด้านบน\n"
                "4. ในช่องค้นหา/Filter พิมพ์ว่า `messages` หรือ `science`\n"
                "5. คลิกสลับห้องแชทใน Discord 1 ครั้ง เพื่อให้เกิดการรับส่งข้อมูล\n"
                "6. คลิกที่ชื่อรายการที่ปรากฏขึ้นมา -> ดูหัวข้อ **Headers (ส่วนหัว)** ด้านขวา\n"
                "7. เลื่อนลงมาที่ **Request Headers** จะพบบรรทัด **`authorization:`**\n"
                "8. **คัดลอกข้อความยาวๆ หลัง authorization:** นั่นคือ Token ของคุณ นำไปส่งบอทได้ทันที!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌟 **วิธีที่ 2: วางคำสั่ง Console 1 บรรทัด (สำหรับคนชอบ F12 Console)**\n"
                "1. ไปที่แท็บ **Console** ใน F12\n"
                "2. ⚠️ **เรื่อง allow pasting:** หากมีคำเตือนสีแดงจาก Discord ให้พิมพ์ `allow pasting` แล้วกด Enter (แม้จะขึ้น SyntaxError สีแดง ไม่ต้องตกใจ นั่นคือเบราว์เซอร์ปลดล็อกการวางแล้ว!)\n"
                "3. คัดลอกโค้ดด้านล่างนี้ วางลงใน Console แล้วกด **Enter**:\n"
                "```javascript\n"
                "(()=>{for(let e of Object.values(webpackChunkdiscord_app.push([[Symbol()],{},e=>e.c])))try{if(!e.exports||e.exports===window)continue;if(e.exports?.getToken)return e.exports.getToken();for(let t in e.exports)if(e.exports?.[t]?.getToken&&\"IntlMessagesProxy\"!==e.exports[t][Symbol.toStringTag])return e.exports[t].getToken()}catch{}})();\n"
                "```\n"
                "4. Token จะแสดงออกมาในเครื่องหมายคำพูด คัดลอกไปส่งบอทได้ทันที\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌟 **วิธีที่ 3: สแกน QR Code ผ่านมือถือ (เร็วสุด ไม่ต้องเปิด F12)**\n"
                "• แนะนำกดปุ่มสีฟ้า **[📷 สแกน QR Code (ดึง Token ออโต้)]** บนแผงควบคุม แล้วเอามือถือเปิด Discord สแกนยืนยัน ได้ Token ทันทีโดยไม่ต้องเปิด F12!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ **ความปลอดภัย:** ข้อความนี้มองเห็นได้เฉพาะคุณ และ**จะทำลายตัวเองภายใน 5 นาที** (<t:{expire_ts}:R>)"
            ),
            color=COLOR_PRIMARY
        )
        embed.set_footer(text="PAYOMBØYZ SECURITY • ไร้ Database ปลอดภัย 100%")

        view = EphemeralActionToolbar(user_id=interaction.user.id, web_url=web_token_url)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        self._schedule_auto_expire(interaction)

    # 📱 ROW 1: BUTTON MOBILE BOOKMARKLET
    @discord.ui.button(
        label="สำหรับ มือถือ (Bookmarklet & Web)",
        style=discord.ButtonStyle.secondary,
        emoji="📱",
        custom_id="pbg_find_token:btn_mobile",
        row=1
    )
    async def btn_mobile(self, interaction: discord.Interaction, button: discord.ui.Button):
        now_ts = int(time.time())
        expire_ts = now_ts + 300
        web_token_url = TOKEN_BRIDGE_URL

        embed = discord.Embed(
            title="📱 วิธีดึง Token บนมือถือ / iPad / แท็บเล็ต (Bookmarklet & Web)",
            description=(
                f"👤 **ผู้ใช้งาน:** {interaction.user.mention} (`{interaction.user.id}`)\n\n"
                "💡 **คำแนะนำที่ดีที่สุดสำหรับมือถือ:**\n"
                "• แนะนำให้ใช้ปุ่ม **\"📷 สแกน QR Code (ดึง Token ออโต้)\"** บนคอมหรืออุปกรณ์อื่น แล้วเอามือถือเครื่องนี้เปิด Discord สแกน จะสะดวกที่สุด ไม่ต้องตั้งค่าอะไรเลย!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌟 **วิธีที่ 1: ดึงผ่าน Bookmarklet บนเว็บเบราว์เซอร์มือถือ**\n"
                "1. เปิดเว็บเบราว์เซอร์ในมือถือ เข้าไปที่: **https://discord.com/app** แล้วล็อกอิน\n"
                "2. ทำการบันทึกหน้านั้นเป็น **Bookmark (ที่คั่นหน้า)** ไว้\n"
                "3. เข้าไปแก้ไข Bookmark นั้น โดยเปลี่ยนช่อง URL ให้เป็นโค้ดด้านล่างนี้:\n"
                "```javascript\n"
                "javascript:(function(){let t=(function(){for(let e of Object.values(webpackChunkdiscord_app.push([[Symbol()],{},e=>e.c])))try{if(!e.exports||e.exports===window)continue;if(e.exports?.getToken)return e.exports.getToken();for(let t in e.exports)if(e.exports?.[t]?.getToken&&\"IntlMessagesProxy\"!==e.exports[t][Symbol.toStringTag])return e.exports[t].getToken()}catch{}})();if(t){prompt(\"คัดลอก Token ของคุณ:\",t)}else{alert(\"ไม่พบ Token กรุณาล็อกอิน Discord Web ก่อน\")}});()\n"
                "```\n"
                "4. กลับไปที่หน้า Discord Web แล้วแตะที่แถบพิมพ์ URL ด้านบน พิมพ์ชื่อ Bookmark แล้วกดรัน\n"
                "5. หน้าจอจะเด้งกล่อง Prompt พร้อม Token ให้คัดลอกได้ทันที!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⏱️ **ความปลอดภัย:** ข้อความนี้มองเห็นได้เฉพาะคุณ และ**จะทำลายตัวเองภายใน 5 นาที** (<t:{expire_ts}:R>)"
            ),
            color=COLOR_SUCCESS
        )
        embed.set_footer(text="PAYOMBØYZ SECURITY • ไร้ Database ปลอดภัย 100%")

        view = EphemeralActionToolbar(user_id=interaction.user.id, web_url=web_token_url)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        self._schedule_auto_expire(interaction)

    def _schedule_auto_expire(self, interaction: discord.Interaction):
        async def expire():
            await asyncio.sleep(300)
            try:
                expired_embed = discord.Embed(
                    title="🔒 เซสชันหมดอายุแล้ว (5 นาที)",
                    description=(
                        "ข้อความแสดงข้อมูลนี้ถูกปิดการใช้งานและทำลายเพื่อความปลอดภัยเรียบร้อยแล้ว\n"
                        "หากต้องการดึงข้อมูลใหม่อีกครั้ง โปรดกดปุ่มเลือกหมวดหมู่ที่แผงข้อความหลัก"
                    ),
                    color=COLOR_EXPIRED
                )
                await interaction.edit_original_response(embed=expired_embed, view=None, attachments=[])
            except Exception:
                pass

        asyncio.create_task(expire())


# ─────────────────────────────────────────────────────────────
# 6. BUILD MAIN PANEL EMBED
# ─────────────────────────────────────────────────────────────
OFFICIAL_TOKEN_FINDER_BANNER = "https://cdn.discordapp.com/attachments/1560993647028076555/1565653893910634556/payomboyz_token_finder.gif"

def build_find_token_panel_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color_hex: Optional[str] = None,
    banner_url: Optional[str] = None
) -> discord.Embed:
    """Build the public persistent panel embed in grand showcase layout."""
    panel_title = title or "🔑 PAYOMBØYZ • ศูนย์ช่วยเหลือดึง Token (Discord Auto Quest)"
    panel_desc = description or (
        "<a:anime_fire:1551069928105447485> **แผงระบบค้นหาและดึง Discord User Token ระดับพรีเมียม**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "แผงระบบดึง Token ความเร็วสูงสำหรับนำไปใช้งานร่วมกับบอท **Discord Auto Quest**\n"
        "*(สำหรับทำเควสเล่นเกม / ดูสตรีม / ปลดล็อกกรอบโปรไฟล์อนิเมะและของรางวัลอัตโนมัติ)*\n\n"
        "<:pbg_run:1551532010932273203> **สถานะระบบ:** `🟢 ONLINE & SECURE (RAM-ONLY)`\n"
        "<a:spin:1551027090025877536> **เวลาประมวลผล:** `⚡ 0.8 - 2.5 วินาที`\n"
        "<a:Sukuna:1551069997999067228> **ระบบความปลอดภัย:** `Zero Retention & Real-time Ephemeral`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    embed_color = COLOR_PRIMARY
    if color_hex:
        try:
            cleaned = color_hex.lstrip("#")
            embed_color = int(cleaned, 16)
        except Exception:
            pass

    embed = discord.Embed(
        title=panel_title,
        description=panel_desc,
        color=embed_color
    )

    embed.set_author(
        name="PAYOMBØYZ AUTOMATION SERVICES • VERIFIED HUB",
        icon_url="https://upload-1.imgz.click/2026/10/payomboyz.rexzy.xyz/cropped_ChatGPTImage20__256907_52_23-1792001768-1792001769.png",
        url="https://discord.gg/KmrgQwbcMD"
    )

    embed.set_thumbnail(
        url="https://upload-1.imgz.click/2026/10/payomboyz.rexzy.xyz/cropped_ChatGPTImage20__256908_58_33_1_-1791693461-1791693461.png"
    )

    embed.add_field(
        name="<:tile40:1551045767383228527> ⚡ วิธีดึง Token ที่ท่านสะดวก (เลือกกดปุ่มด้านล่าง):",
        value=(
            "• 📷 **สแกน QR Code (แนะนำสูงสุด 100%)**: กดปุ่มสีม่วง `สแกน QR Code` แล้วเอามือถือเปิด Discord แตะสแกนยืนยัน Token จะเด้งขึ้นมาทันที ไร้ Captcha 100%!\n"
            "• 💻 **สำหรับ PC (ดึงผ่าน Console 5 วิ)**: เปิด DevTools บนคอม วางโค้ด 1 บรรทัด ได้ Token ทันที ปลอดภัยและรวดเร็ว\n"
            "• 📱 **สำหรับ มือถือ (Bookmarklet)**: วิธีดึงผ่าน Bookmarklet บนเว็บเบราว์เซอร์มือถือ สะดวกไม่ต้องโหลดแอปเพิ่ม\n"
            "• 🔓 **ล็อกอินดึง Token (Direct Auth)**: กรอก Email และ Password ผ่านป๊อปอัปของบอทเพื่อดึง Token ทันที"
        ),
        inline=False
    )

    embed.add_field(
        name="🚀 ระบบ 1-Click Sync เข้า Auto Quest อัตโนมัติ:",
        value=(
            "เมื่อท่านดึง Token สำเร็จ ระบบจะแสดงปุ่มสีเขียว **[🚀 ส่ง Token ไปทำ Auto Quest ทันที]**\n"
            "สามารถคลิกส่งให้ระบบเริ่มทำเควสและรับรางวัลให้ทันที โดยไม่ต้องก็อปปี้หรือสลับหน้าต่าง!"
        ),
        inline=False
    )

    embed.add_field(
        name="🛡️ เงื่อนไขและการรักษาความปลอดภัย (Zero Retention Guarantee):",
        value=(
            "```yaml\n"
            "1. ระบบนี้ไม่มี Database ข้อมูลรหัสผ่านและ Token ประมวลผลใน RAM ชั่วคราวเท่านั้น\n"
            "2. ผู้ใช้งานจะได้รับและมองเห็นเฉพาะ Token ของตัวเอง (ข้อความเห็นคนเดียว Ephemeral)\n"
            "3. มีระบบปิดการใช้งานและทำลายข้อความอัตโนมัติภายใน 5 นาที เพื่อความปลอดภัยสูงสุด\n"
            "```"
        ),
        inline=False
    )

    embed.add_field(
        name="⚠️ คำเตือนสำคัญ:",
        value="> Token เปรียบเสมือนกุญแจบัญชี Discord ของคุณ โปรดเก็บรักษาให้ดีและอย่านำไปส่งต่อให้บุคคลอื่นเด็ดขาด!",
        inline=False
    )

    final_banner = banner_url or OFFICIAL_TOKEN_FINDER_BANNER
    if final_banner and final_banner.startswith("http"):
        embed.set_image(url=final_banner)

    embed.set_footer(
        text="PAYOMBØYZ DISCORD QUEST HELPER • Zero Retention Architecture",
        icon_url="https://upload-1.imgz.click/2026/10/payomboyz.rexzy.xyz/cropped_ChatGPTImage20__256907_52_23-1792001768-1792001769.png"
    )
    return embed


# ─────────────────────────────────────────────────────────────
# 7. COG REGISTRATION
# ─────────────────────────────────────────────────────────────
class TokenFinderCog(commands.Cog, name="TokenFinder"):
    """🔑 ศูนย์ช่วยเหลือและดึง Token Discord สำหรับ Auto Quest"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="find_token",
        description="🔑 ส่งแผงช่วยเหลือและระบบดึง Discord User Token สำหรับ Auto Quest"
    )
    @app_commands.describe(
        channel="ช่องที่ต้องการส่งแผงข้อความ (เว้นว่างเพื่อส่งในช่องปัจจุบัน)",
        title="หัวข้อของแผงข้อความ (ไม่บังคับ)",
        description="รายละเอียดในแผงข้อความ (ไม่บังคับ)",
        banner_url="ลิงก์รูปภาพ GIF หรือ Banner ขนาดเต็ม (เว้นว่างเพื่อใช้ GIF เริ่มต้น)",
        color="รหัสสี HEX เช่น #5865F2 (ไม่บังคับ)"
    )
    @app_commands.default_permissions(administrator=True)
    async def cmd_find_token(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        banner_url: Optional[str] = None,
        color: Optional[str] = None
    ):
        target_ch = channel or interaction.channel
        if not target_ch or not hasattr(target_ch, "send"):
            return await interaction.response.send_message("❌ ไม่สามารถส่งข้อความในช่องที่เลือกได้", ephemeral=True)

        embed = build_find_token_panel_embed(title=title, description=description, color_hex=color, banner_url=banner_url)
        view = FindTokenPanelView()
        await target_ch.send(embed=embed, view=view)

        await interaction.response.send_message(
            f"✅ ส่งแผงดึง Token ไปยังช่อง {target_ch.mention} สำเร็จเรียบร้อยแล้ว!",
            ephemeral=True
        )

    @app_commands.command(
        name="token",
        description="🔑 เปิดหน้าต่างช่วยเหลือดึง Token สำหรับใช้งาน Auto Quest (เห็นเฉพาะคุณ)"
    )
    async def cmd_token_shortcut(self, interaction: discord.Interaction):
        embed = build_find_token_panel_embed()
        view = FindTokenPanelView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(TokenFinderCog(bot))
    print("  [OK] Loaded Cog: TokenFinderCog (/find_token, /token)")
