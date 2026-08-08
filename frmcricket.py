import logging
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "8049311684:AAHBcOkfaY1MutqZoB24HxjJOpUK0GUW668"
GCS_WEB_APP_URL = "https://tannuxshaan-cmyk.github.io/CRICKET-BOT/"

WELCOME_TEXT = (
    "🏏 **Welcome to Ultimate Hand Cricket Bot!** 🎮\n\n"
    "Add me to your group chat and start a match with your friends!\n\n"
    "👥 **Team Mode (For GC):**\n"
    "• `/create_teams` - Create Team A & Team B\n"
    "• `/join_teama` - Join Team A 🔴\n"
    "• `/join_teamb` - Join Team B 🔵\n"
    "• `/teams` - View current players roster\n"
    "• `/set_overs <number>` - Set match overs\n\n"
    "⚡ **Gameplay & Live Score:**\n"
    "• `/joingame` - Start a solo/group match session\n"
    "• `/score` - Check live match score\n"
    "• `/endgame` - Stop/Reset current match\n\n"
    "👤 **Profile & Stats:**\n"
    "• `/userinfo` | `/stats` | `/user_ranks`"
)

def init_db():
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            total_runs INTEGER DEFAULT 0,
            matches_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_matches (
            chat_id INTEGER PRIMARY KEY,
            team_a_name TEXT DEFAULT 'Team A',
            team_b_name TEXT DEFAULT 'Team B',
            overs INTEGER DEFAULT 5,
            current_innings INTEGER DEFAULT 1,
            batting_team TEXT DEFAULT 'Team A',
            team_a_score INTEGER DEFAULT 0,
            team_b_score INTEGER DEFAULT 0,
            team_a_wickets INTEGER DEFAULT 0,
            team_b_wickets INTEGER DEFAULT 0,
            match_status TEXT DEFAULT 'waiting'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Temporary memory for team members in chats
group_teams = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 Play Mini App", web_app=WebAppInfo(url=GCS_WEB_APP_URL))],
        [InlineKeyboardButton("📖 Help & Commands", callback_data="help_menu")]
    ]
    await update.message.reply_text(WELCOME_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")

async def create_teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    group_teams[chat_id] = {"Team A": [], "Team B": [], "overs": 5}
    
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO group_matches (chat_id, match_status) VALUES (?, ?)", (chat_id, "forming"))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        "👥 **Teams Created for this Group!**\n\n"
        "Players can now join using:\n"
        "👉 `/join_teama` (Join Team A 🔴)\n"
        "👉 `/join_teamb` (Join Team B 🔵)"
    )

async def join_teamA(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user.first_name
    if chat_id not in group_teams:
        group_teams[chat_id] = {"Team A": [], "Team B": [], "overs": 5}
    
    if user not in group_teams[chat_id]["Team A"]:
        group_teams[chat_id]["Team A"].append(user)
    await update.message.reply_text(f"🔴 **{user}** joined Team A!")

async def join_teamB(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user.first_name
    if chat_id not in group_teams:
        group_teams[chat_id] = {"Team A": [], "Team B": [], "overs": 5}
    
    if user not in group_teams[chat_id]["Team B"]:
        group_teams[chat_id]["Team B"].append(user)
    await update.message.reply_text(f"🔵 **{user}** joined Team B!")

async def teams_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    teams = group_teams.get(chat_id, {"Team A": [], "Team B": []})
    t_a = ", ".join(teams["Team A"]) if teams["Team A"] else "No players yet"
    t_b = ", ".join(teams["Team B"]) if teams["Team B"] else "No players yet"
    
    await update.message.reply_text(
        f"📋 **Current Group Match Roster:**\n\n"
        f"🔴 **Team A:** {t_a}\n"
        f"🔵 **Team B:** {t_b}"
    )

async def set_overs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if context.args:
        try:
            ovs = int(context.args[0])
            if chat_id in group_teams:
                group_teams[chat_id]["overs"] = ovs
            await update.message.reply_text(f"⚙️ Match overs successfully set to **{ovs}** overs.")
        except ValueError:
            await update.message.reply_text("⚠️ Please provide a valid number, e.g., `/set_overs 5`")
    else:
        await update.message.reply_text("⚠️ Please specify overs, e.g., `/set_overs 5`")

async def joingame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1 Run", callback_data="run_1"), InlineKeyboardButton("2 Runs", callback_data="run_2"), InlineKeyboardButton("3 Runs", callback_data="run_3")],
        [InlineKeyboardButton("4 Runs ⚡", callback_data="run_4"), InlineKeyboardButton("6 Runs 💥", callback_data="run_6")]
    ]
    await update.message.reply_text(
        "🏏 **Hand Cricket Match Started!**\nClick your shot below to score runs:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT team_a_score, team_a_wickets, team_b_score, team_b_wickets, batting_team FROM group_matches WHERE chat_id = ?", (chat_id,))
    match = cursor.fetchone()
    conn.close()
    
    if match:
        t_a_sc, t_a_w, t_b_sc, t_b_w, batting = match
        await update.message.reply_text(
            f"📊 **Live Scoreboard:**\n\n"
            f"🔴 Team A: {t_a_sc} / {t_a_w}\n"
            f"🔵 Team B: {t_b_sc} / {t_b_w}\n\n"
            f"⚡ Currently Batting: **{batting}**"
        )
    else:
        await update.message.reply_text("⚠️ No active match in this group. Use `/create_teams` or `/joingame` to start!")

async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT total_runs, matches_played, wins FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()
    
    runs = row[0] if row else 0
    played = row[1] if row else 0
    wins = row[2] if row else 0
    
    await update.message.reply_text(
        f"👤 **Player Profile:**\n"
        f"• Name: {user.first_name}\n"
        f"• Total Runs: 🏏 {runs}\n"
        f"• Matches Played: {played}\n"
        f"• Wins: 🏆 {wins}"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await userinfo(update, context)

async def user_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, total_runs FROM users ORDER BY total_runs DESC LIMIT 5")
    top_users = cursor.fetchall()
    conn.close()
    
    txt = "🏆 **Global Leaderboard (Top Players):**\n\n"
    for idx, (uname, runs) in enumerate(top_users, 1):
        txt += f"{idx}. {uname or 'Player'} — 🏏 {runs} Runs\n"
    await update.message.reply_text(txt)

async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM group_matches WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    
    if chat_id in group_teams:
        del group_teams[chat_id]
        
    await update.message.reply_text("🛑 Match session ended and data cleared successfully.")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "help_menu":
        await query.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")
    elif data.startswith("run_"):
        user_run = int(data.split("_")[1])
        bot_run = random.randint(1, 6)
        
        if user_run == bot_run:
            await query.edit_message_text(f"❌ **OUT!** You chose {user_run}, Bot/Bowler threw {bot_run}. Inning over!")
        else:
            await query.edit_message_text(f"⚡ Great shot! You scored **{user_run} runs** | Ball bowl choice: {bot_run}")

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handlers([
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("create_teams", create_teams),
        CommandHandler("join_teama", join_teamA),
        CommandHandler("join_teamb", join_teamB),
        CommandHandler("teams", teams_list),
        CommandHandler("set_overs", set_overs),
        CommandHandler("joingame", joingame),
        CommandHandler("score", score),
        CommandHandler("userinfo", userinfo),
        CommandHandler("stats", stats),
        CommandHandler("user_ranks", user_ranks),
        CommandHandler("endgame", endgame),
        CallbackQueryHandler(handle_buttons)
    ])
    application.run_polling()