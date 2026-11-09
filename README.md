# Azkar Reminders for Android (أذكار الصباح والمساء)

Every day after **Fajr** you get أذكار الصباح, and after **Asr** you get أذكار المساء,
on every Android phone you add and on its Galaxy Watch.

**You do Part A only once. Then do Part B on each phone (2 minutes each).**

---

## Part A: One-time setup (about 10 minutes, on a computer)

1. **Pick a secret name** for your group, long and random.
   Example: `azkar-family-7h2k9q4x`. Write it down; every phone will use it.

2. **Make a free GitHub account** at github.com.

3. **Create a new repository**: click **+** → **New repository** → name it `azkar` →
   choose **Private** → **Create**.

4. **Upload the files**: click **uploading an existing file** and drag in
   everything from this folder (`azkar.json`, `send_azkar.py`, `README.md` and the
   `.github` folder) → **Commit changes**.

5. **Add your secret name**: **Settings** → **Secrets and variables** → **Actions** →
   **New repository secret**
   - Name: `NTFY_TOPIC`
   - Secret: your secret name from step 1

That's it. From now on it runs by itself every night.

---

## Part B: On each Android phone (2 minutes)

1. Install **ntfy** from the Play Store.
2. Open it → tap **+** → type your secret name → **Subscribe**.
3. Stop the phone from putting ntfy to sleep:
   **Settings → Apps → ntfy → Battery → Unrestricted**.
4. **Galaxy Watch** (if you have one): open **Galaxy Wearable** → **Watch settings** →
   **Notifications** → turn on **ntfy** and **Show while using phone**.

Repeat for every phone. All phones get the same azkar at the same time.

---

## Test it

On GitHub: **Actions** tab → **Azkar reminders** → **Run workflow** → choose **test** → **Run**.
Within a few seconds every phone should get 3 notifications.

---

## Good to know
- Default city is **Riyadh**. Azkar start **15 minutes after the adhan**.
  To change these, go to **Settings → Secrets and variables → Actions → Variables** and add
  `CITY`, `COUNTRY`, or `SABAH_OFFSET_MIN` / `MASA_OFFSET_MIN` (minutes).
- To remove a phone, unsubscribe in its ntfy app. To add one, repeat Part B.
- Anyone who knows your secret name can receive the azkar, so share it only with family.
- To change the azkar, edit `azkar.json` on GitHub.
