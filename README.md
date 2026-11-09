# Azkar Reminders on Telegram (أذكار الصباح والمساء)

Every day, a Telegram bot posts أذكار الصباح **15 minutes after Fajr** and
أذكار المساء **15 minutes after Asr** (Riyadh time, updated daily) to your
Telegram channel. Anyone who joins the channel gets them on Android, iPhone,
Galaxy Watch and Apple Watch.

## Part 1: Telegram (5 minutes, on your phone)

**Create the bot**
1. In Telegram, search **@BotFather** (blue check ✔) and open it.
2. Send `/newbot`.
3. Send a name, for example `Azkar Bot`.
4. Send a username ending in `bot`, for example `azkar_hussain_bot`.
5. BotFather replies with a **token** (looks like `123456789:ABCdef...`). Copy it.

**Create the channel**
1. Tap ✏️ (new message) → **New Channel** → name it, for example `أذكار الصباح والمساء`.
2. Choose **Public** and pick a link, for example `t.me/azkar_hussain`.
   (Private works too; see the end.)
3. Open the channel → tap its name → **Administrators** → **Add Admin** →
   search your bot's username → **Done** / ✓.

## Part 2: GitHub (5 minutes)

1. **Upload the new files.** In your `azkar` repository:
   - Click `send_azkar.py` → ✏️ → select all → paste the new file → **Commit changes**.
   - Open `.github/workflows/azkar.yml` → ✏️ → select all → paste the new file → **Commit changes**.
   - Same for `README.md` (optional).
2. **Make the repository public.** It has to wait before each prayer, and that
   is only free for public repositories. Your token stays hidden.
   **Settings → General** → scroll to the bottom → **Change visibility** → **Public**.
3. **Add two secrets.** **Settings → Secrets and variables → Actions → New repository secret**:
   | Name | Secret |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | the token from BotFather |
   | `TELEGRAM_CHAT` | `@` + your channel link name, for example `@azkar_hussain` |
4. Delete the old `NTFY_TOPIC` secret (🗑).

## Part 3: Test
**Actions → Azkar reminders → Run workflow → test → Run workflow.**
A "✅ تم الربط بنجاح" message should appear in your channel.
To see the full azkar now, run it again with **sabah-now** or **masa-now**.

## Part 4: Each family member
1. Open the channel link (for example `t.me/azkar_hussain`) → **Join**.
2. Make sure the channel is **not muted** (tap the channel name → 🔔 on).
3. **Galaxy Watch:** Galaxy Wearable → Notifications → turn on **Telegram** and **Show while using phone**.
4. **Apple Watch:** iPhone **Watch** app → Notifications → **Telegram** → Mirror my iPhone.
5. **iPhone at Fajr:** Settings → Focus → **Sleep** → Apps → add **Telegram**.

## Private channel instead of public
Make the bot an admin as above, then post any message in the channel.
On GitHub run the workflow with **find-chat-id**, open the run → **azkar** →
**Post azkar to Telegram**. Copy the number shown (starts with `-100`) and use
it as the `TELEGRAM_CHAT` secret instead of `@name`.
