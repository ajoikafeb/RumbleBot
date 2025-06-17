# 🤖 RUMBLE Bot — Discord Survival Game

**RUMBLE Bot** adalah bot survival interaktif berbasis teks yang dirancang khusus untuk komunitas Discord. Bot ini menyimulasikan pertarungan antar pemain dalam ronde-ronde eliminasi, lengkap dengan fitur revive, mass kill, dan leaderboard most kill.

## 🎮 Fitur Utama

- 🔘 Tombol join yang interaktif
- ⏳ Hitung mundur pendaftaran secara real-time (2 atau 5 menit)
- ⚔️ Eliminasi acak setiap ronde (2–5 pemain per ronde)
- 💀 Event Mass Kill (5–15% pemain terbunuh secara misterius)
- ♻️ Revive Mode (opsional, aktif di pertengahan game)
- 🏆 Statistik akhir:
  - Pemenang tunggal
  - Top 5 survivor terakhir
  - Top 5 pembunuh terbanyak
- 🛡️ Sistem role-based admin control
- ⚙️ Slash command interface

## 📜 Commands

| Perintah        | Deskripsi                                                                 |
|-----------------|---------------------------------------------------------------------------|
| `/rumble`       | Memulai game dengan durasi dan mode revive (admin only)                  |
| `/start`        | Memulai game secara manual sebelum waktu habis (admin only)              |
| `/stop`         | Menghentikan game RUMBLE (admin only)                                     |
| `/search`       | Menelusuri siapa yang membunuh seorang pemain tertentu                   |

## 🔐 Role Admin

Bot hanya dapat dikendalikan oleh user dengan role ID tertentu. Kamu bisa atur di bagian berikut:

```python
ADMIN_ROLE_IDS = [
    1381509311024337008,  # 👑 Owner
    1362624947557503006,  # 🛡️ Moderator
    1384176855292313741   # ⚙️ Tester
]
