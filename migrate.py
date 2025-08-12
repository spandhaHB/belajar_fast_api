#!/usr/bin/env python3
"""
Script untuk mengelola migrasi database
Penggunaan: python migrate.py [command]

Commands:
- upgrade: Jalankan semua migrasi ke versi terbaru
- downgrade: Turunkan migrasi 1 step
- current: Tampilkan versi migrasi saat ini
- history: Tampilkan riwayat migrasi
- stamp: Tandai database dengan versi tertentu tanpa menjalankan migrasi
- revision: Buat file migrasi baru
"""
import sys
import subprocess
import os
from database import check_db_connection

def run_alembic_command(command_args):
    """Jalankan perintah alembic"""
    try:
        result = subprocess.run(['alembic'] + command_args, capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Gagal menjalankan alembic: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    # Cek koneksi database sebelum migrasi
    print("Memeriksa koneksi database...")
    if not check_db_connection():
        print("❌ Koneksi database gagal! Periksa konfigurasi database di .env")
        return
    print("✅ Koneksi database berhasil!")
    
    if command == 'upgrade':
        print("🚀 Menjalankan migrasi ke versi terbaru...")
        if run_alembic_command(['upgrade', 'head']):
            print("✅ Migrasi berhasil!")
        else:
            print("❌ Migrasi gagal!")
    
    elif command == 'downgrade':
        print("⬇️  Menurunkan migrasi 1 step...")
        if run_alembic_command(['downgrade', '-1']):
            print("✅ Downgrade berhasil!")
        else:
            print("❌ Downgrade gagal!")
    
    elif command == 'current':
        print("📍 Versi migrasi saat ini:")
        run_alembic_command(['current'])
    
    elif command == 'history':
        print("📜 Riwayat migrasi:")
        run_alembic_command(['history', '--verbose'])
    
    elif command == 'stamp':
        if len(sys.argv) < 3:
            print("Usage: python migrate.py stamp <revision>")
            print("Contoh: python migrate.py stamp head")
            return
        revision = sys.argv[2]
        print(f"🏷️  Menandai database dengan versi {revision}...")
        if run_alembic_command(['stamp', revision]):
            print("✅ Stamp berhasil!")
        else:
            print("❌ Stamp gagal!")
    
    elif command == 'revision':
        if len(sys.argv) < 3:
            print("Usage: python migrate.py revision <message>")
            print("Contoh: python migrate.py revision 'Add new column'")
            return
        message = sys.argv[2]
        print(f"📝 Membuat file migrasi baru: {message}")
        if run_alembic_command(['revision', '--autogenerate', '-m', message]):
            print("✅ File migrasi baru berhasil dibuat!")
        else:
            print("❌ Gagal membuat file migrasi!")
    
    elif command == 'reset':
        print("🔄 Reset database (downgrade ke base lalu upgrade ke head)...")
        print("Menurunkan ke base...")
        if run_alembic_command(['downgrade', 'base']):
            print("Menaikkan ke head...")
            if run_alembic_command(['upgrade', 'head']):
                print("✅ Reset database berhasil!")
            else:
                print("❌ Upgrade setelah reset gagal!")
        else:
            print("❌ Downgrade ke base gagal!")
    
    else:
        print(f"Command '{command}' tidak dikenali.")
        print(__doc__)

if __name__ == '__main__':
    main()









