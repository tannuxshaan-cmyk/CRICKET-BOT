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
GCS_WEB_APP_URL = "https://your-username.github.io/your-repo-name/index.html"

WELCOME_TEXT = (
    "🔥 **WELCOME TO ULTIMATE CRICKET ARENA** 🔥\n\n"
    "👋 Hello **{name}**! Get ready for the most advanced Hand Cricket experience.\n\n"
    "✨ **Main Features:**\n"
    "• ⚔️ **1v1 IRL Duel:** `/duel` - Toss, overs, wickets & live commentary.\n"
    "• 👥 **Team Play:** `/create_teams`, `/join_teama`, `/join_teamb`, `/teams`\n"
    "• 👤 **Profile & Stats:** `/stats`, `/userinfo`, `/user_ranks`\n\n"
    "🎽 **Set your unique jersey number now using:** `/jersey <number>`"
)

def init_db():
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            jersey_number INTEGER UNIQUE,
            lang TEXT DEFAULT 'en',
            matches_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            total_runs INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 100
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_matches (
            chat_id INTEGER PRIMARY KEY,
            player1_id INTEGER,
            player1_name TEXT,
            player2_id INTEGER,
            player2_name TEXT,
            player1_score INTEGER DEFAULT 0,
            player2_score INTEGER DEFAULT 0,
            player1_wickets INTEGER DEFAULT 0,
            player2_wickets INTEGER DEFAULT 0,
            current_batter INTEGER,
            current_ball INTEGER DEFAULT 0,
            max_balls INTEGER DEFAULT 30,
            innings INTEGER DEFAULT 1,
            match_status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT jersey_number FROM users WHERE user_id = ?", (user.id,))
    res = cursor.fetchone()
    
    if not res:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, lang) VALUES (?, ?, ?)", (user.id, user.first_name, 'en'))
        conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("✅ Pick Jersey", callback_data="pick_jersey")],
        [InlineKeyboardButton("🎮 Play Mini App", web_app=WebAppInfo(url=GCS_WEB_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    txt = WELCOME_TEXT.format(name=user.first_name)
    await update.message.reply_text(
        txt,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📋 **Advanced Command Center:**\n\n"
        "🟢 **General:** /start, /help, /play, /duel, /jersey <no>\n"
        "👥 **Teams:** /create_teams, /join_teama, /join_teamb, /teams, /set_overs\n"
        "👤 **Solo & Profile:** /joingame, /score, /stats, /userinfo, /user_ranks\n"
        "🛑 **Control:** /endgame"
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text, parse_mode="Markdown")

async def set_jersey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            j_no = int(context.args[0])
            user_id = update.effective_user.id
            conn = sqlite3.connect("cricket_bot.db")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE jersey_number = ?", (j_no,))
            taken = cursor.fetchone()
            if taken:
                await update.message.reply_text(f"⚠️ Jersey #{j_no} is already taken by someone else!")
            else:
                cursor.execute("UPDATE users SET jersey_number = ? WHERE user_id = ?", (j_no, user_id))
                conn.commit()
                await update.message.reply_text(f"🎉 Awesome! Your unique jersey number is successfully set to: **#{j_no}** 🎽")
            conn.close()
        except ValueError:
            await update.message.reply_text("⚠️ Please enter a valid number, e.g., `/jersey 18`")
    else:
        await update.message.reply_text("⚠️ Please provide a number, e.g., `/jersey 7`")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👤 Solo Quick Match", callback_data="play_solo")],
        [InlineKeyboardButton("👥 Team Match Mode", callback_data="play_team")]
    ]
    await update.message.reply_text("🎮 Select your game mode:", reply_markup=InlineKeyboardMarkup(keyboard))

teams_data = {"Team A": [], "Team B": [], "overs": 5}

async def create_teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teams_data["Team A"] = []
    teams_data["Team B"] = []
    await update.message.reply_text("👥 Teams reset & created! Join using `/join_teama` or `/join_teamb`.")

async def join_teamA(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    if user not in teams_data["Team A"]:
        teams_data["Team A"].append(user)
    await update.message.reply_text(f"✅ {user} joined **Team A** 🔴.")

async def join_teamB(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    if user not in teams_data["Team B"]:
        teams_data["Team B"].append(user)
    await update.message.reply_text(f"✅ {user} joined **Team B** 🔵.")

async def teams_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t_a = ", ".join(teams_data["Team A"]) if teams_data["Team A"] else "Empty"
    t_b = ", ".join(teams_data["Team B"]) if teams_data["Team B"] else "Empty"
    await update.message.reply_text(f"👥 **Current Roster:**\n🔴 Team A: {t_a}\n🔵 Team B: {t_b}")

async def set_overs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            ovs = int(context.args[0])
            teams_data["overs"] = ovs
            await update.message.reply_text(f"⚙️ Match overs configured to: {ovs} overs")
        except ValueError:
            await update.message.reply_text("⚠️ Enter a valid number, e.g., `/set_overs 5`")
    else:
        await update.message.reply_text("⚠️ Please specify overs, e.g., `/set_overs 5`")

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1", callback_data="run_1"), InlineKeyboardButton("2", callback_data="run_2"), InlineKeyboardButton("3", callback_data="run_3")],
        [InlineKeyboardButton("4", callback_data="run_4"), InlineKeyboardButton("6", callback_data="run_6")]
    ]
    await update.message.reply_text("🏏 Solo Hand Cricket Arena Active! Choose your run:", reply_markup=InlineKeyboardMarkup(keyboard))

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    max_balls = int(teams_data.get("overs", 5)) * 6
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM active_matches WHERE chat_id = ?", (chat_id,))
    match = cursor.fetchone()
    if not match:
        cursor.execute("INSERT INTO active_matches (chat_id, player1_id, player1_name, max_balls, match_status) VALUES (?, ?, ?, ?, ?)", 
                       (chat_id, user.id, user.first_name, max_balls, "waiting"))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"🏟️ **{user.first_name}** created an IRL Duel Match!\nClick below to enter the battle:", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ Join Duel Match", callback_data="join_duel_match")]]))
    else:
        conn.close()
        await update.message.reply_text("⚠️ A match is already running in this chat.")

async def handle_game_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    chat_id = query.message.chat_id

    if data == "pick_jersey":
        await query.edit_message_text("🎽 **To set your jersey number, send:**\n`/jersey <your_number>` in the chat.")
    
    elif data == "join_duel_match":
        conn = sqlite3.connect("cricket_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT player1_id, player1_name FROM active_matches WHERE chat_id = ? AND match_status = ?", (chat_id, "waiting"))
        match = cursor.fetchone()
        if match:
            p1_id, p1_name = match
            if p1_id == user.id:
                await query.answer("You cannot join your own match!", show_alert=True)
                conn.close()
                return
            cursor.execute("UPDATE active_matches SET player2_id = ?, player2_name = ?, match_status = ? WHERE chat_id = ?", (user.id, user.first_name, "playing", chat_id))
            conn.commit()
            conn.close()
            await query.edit_message_text("🪙 **TOSS COMPLETED!** Choose your priority:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏏 Batting", callback_data="toss_bat"), InlineKeyboardButton("⚾ Bowling", callback_data="toss_bowl")]]))
        else:
            conn.close()
            await query.answer("Match already started or expired.", show_alert=True)

    elif data.startswith("run_"):
        user_run = int(data.split("_")[1])
        bot_run = random.randint(1, 6)
        result = f"❌ **OUT!** You threw {user_run}, Bot threw {bot_run}." if user_run == bot_run else f"⚡ You scored: **{user_run}** | Bot choice: {bot_run}"
        await query.edit_message_text(result)

    elif data.startswith("irl_"):
        run = int(data.split("_")[1])
        await query.edit_message_text(f"🏏 Shot registered: {run} runs. Processing delivery...")

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT player1_name, player2_name, player1_score, player2_score, player1_wickets, player2_wickets, innings FROM active_matches WHERE chat_id = ?", (chat_id,))
    match = cursor.fetchone()
    conn.close()
    if match:
        p1_n, p2_n, p1_sc, p2_sc, p1_w, p2_w, inn = match
        await update.message.reply_text(f"📊 **Live Match Score (Innings {inn}):**\n🔴 {p1_n}: {p1_sc}/{p1_w}\n🔵 {p2_n}: {p2_sc}/{p2_w}")
    else:
        await update.message.reply_text("📊 No active match found in this chat. Start one using `/duel`!")

async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT jersey_number, coins FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()
    jersey = row[0] if row and row[0] else "Not Set"
    coins = row[1] if row else 100
    await update.message.reply_text(f"👤 **User Profile Card:**\n• Name: {user.first_name}\n• ID: `{user.id}`\n• 🎽 Jersey: #{jersey}\n• 🪙 Coins: {coins}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT matches_played, wins, total_runs, jersey_number FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        played, wins, runs, jersey = row
        j_text = f"#{jersey}" if jersey else "Not Set"
        
        badges = []
        if runs >= 500: badges.append("🔥 Century Master")
        if wins >= 5: badges.append("🏆 Pro Champion")
        if not badges: badges.append("⭐ Rookie Contender")
        
        await update.message.reply_text(
            f"📊 **Career Statistics & Badges:**\n\n"
            f"• 🎽 Jersey: {j_text}\n"
            f"• Matches Played: {played}\n"
            f"• Total Wins: {wins}\n"
            f"• Total Runs Scored: {runs}\n\n"
            f"🏅 **Badges Unlocked:**\n" + "\n".join([f" - {b}" for b in badges])
        )
    else:
        await update.message.reply_text("⚠️ Profile data not found. Please type `/start` first.")

async def user_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, total_runs, jersey_number FROM users ORDER BY total_runs DESC LIMIT 10")
    top_users = cursor.fetchall()
    conn.close()
    
    leaderboard_text = "🏆 **Global Leaderboard (Top Players):**\n\n"
    if top_users:
        for idx, (uname, runs, jersey) in enumerate(top_users, 1):
            j_str = f"(#{jersey})" if jersey else ""
            leaderboard_text += f"{idx}. **{uname or 'Player'}** {j_str} — 🏏 {runs} Runs\n"
    else:
        leaderboard_text += "No records found yet."
        
    await update.message.reply_text(leaderboard_text, parse_mode="Markdown")

async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_matches WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("🛑 Active match session successfully terminated & reset.")

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handlers([
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("play", play),
        CommandHandler("duel", duel),
        CommandHandler("jersey", set_jersey_command),
        CommandHandler("create_teams", create_teams),
        CommandHandler("join_teama", join_teamA),
        CommandHandler("join_teamb", join_teamB),
        CommandHandler("teams", teams_list),
        CommandHandler("set_overs", set_overs),
        CommandHandler("joingame", join_game),
        CommandHandler("score", score),
        CommandHandler("stats", stats),
        CommandHandler("userinfo", userinfo),
        CommandHandler("user_ranks", user_ranks),
        CommandHandler("endgame", endgame),
        CallbackQueryHandler(handle_game_buttons)
    ])
    application.run_polling()