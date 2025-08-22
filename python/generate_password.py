#!/usr/bin/env python3
"""
パスワード管理ツール - 3段階セキュリティ
- 初回: 自由に実行可能（管理者アカウント作成）
- 2回目以降: 認証またはリカバリーキーが必要
使い方: python generate_password.py [オプション]
"""

from werkzeug.security import generate_password_hash, check_password_hash
import getpass
import json
import os
import sys
import argparse
import secrets
from datetime import datetime

CONFIG_FILE = 'config/auth_users.json'
RECOVERY_FILE = 'config/.recovery_key'


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description='Mercury Mapping Engine - パスワード管理ツール')
    parser.add_argument('--reset', action='store_true', help='パスワードリセット（リカバリーキーが必要）')
    parser.add_argument('--add-user', action='store_true', help='新規ユーザー追加（管理者認証が必要）')
    parser.add_argument('--recovery-key', type=str, help='リカバリーキー')
    parser.add_argument('--list-users', action='store_true', help='ユーザー一覧表示（管理者認証が必要）')
    args = parser.parse_args()
    
    # ファイルパスを絶対パスに変換
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, CONFIG_FILE)
    recovery_path = os.path.join(script_dir, RECOVERY_FILE)
    
    print("=" * 60)
    print("🔐 Mercury Mapping Engine - パスワード管理システム")
    print("=" * 60)
    
    # 初回セットアップチェック
    if not os.path.exists(config_path):
        print("\n🎉 初回セットアップモードを開始します")
        initial_setup(config_path, recovery_path)
        return
    
    # 既存システムの場合
    if args.reset:
        # リカバリーモード
        if not args.recovery_key:
            recovery_key = getpass.getpass("🔑 リカバリーキーを入力してください: ")
        else:
            recovery_key = args.recovery_key
            
        if verify_recovery_key(recovery_key, recovery_path):
            print("✅ リカバリーキー認証成功")
            reset_password(config_path)
        else:
            print("❌ リカバリーキーが無効です")
            sys.exit(1)
    
    elif args.add_user:
        # 管理者認証モード
        if authenticate_admin(config_path):
            add_new_user(config_path)
        else:
            print("❌ 管理者認証に失敗しました")
            sys.exit(1)
    
    elif args.list_users:
        # ユーザー一覧表示
        if authenticate_admin(config_path):
            list_users(config_path)
        else:
            print("❌ 管理者認証に失敗しました")
            sys.exit(1)
    
    else:
        print("\n⚠️  既にセットアップ済みです")
        print("\n利用可能なオプション:")
        print("  --add-user              : 新規ユーザー追加（管理者権限必要）")
        print("  --list-users            : ユーザー一覧表示（管理者権限必要）")
        print("  --reset --recovery-key  : パスワードリセット（リカバリーキー必要）")
        print("\n例:")
        print("  python generate_password.py --add-user")
        print("  python generate_password.py --reset --recovery-key REC-XXXXXXXX")
        sys.exit(1)


def initial_setup(config_path, recovery_path):
    """初回セットアップ"""
    print("\nMercury Mapping Engineの認証システムをセットアップします。")
    print("最初に管理者アカウントを作成してください。\n")
    
    # リカバリーキー生成
    recovery_key = f"REC-{secrets.token_hex(8).upper()}"
    
    print("=" * 60)
    print("⚠️  重要: リカバリーキーを安全な場所に保管してください")
    print("=" * 60)
    print(f"\n📝 リカバリーキー: {recovery_key}\n")
    print("このキーは画面に一度しか表示されません。")
    print("パスワードを忘れた場合の復旧に必要です。")
    print("=" * 60)
    
    input("\n↵ Enterキーを押して続行...")
    
    # リカバリーキーをハッシュ化して保存
    os.makedirs(os.path.dirname(recovery_path), exist_ok=True)
    with open(recovery_path, 'w') as f:
        recovery_hash = generate_password_hash(recovery_key)
        json.dump({
            'recovery_hash': recovery_hash,
            'created_at': datetime.now().isoformat()
        }, f)
    
    # 管理者アカウント作成
    print("\n👤 管理者アカウントを作成します")
    username = input("管理者のユーザー名 [admin]: ").strip() or "admin"
    
    while True:
        password = getpass.getpass("パスワード: ")
        if len(password) < 8:
            print("❌ パスワードは8文字以上で設定してください")
            continue
        
        password_confirm = getpass.getpass("パスワード（確認）: ")
        if password != password_confirm:
            print("❌ パスワードが一致しません")
            continue
        break
    
    display_name = input("表示名 [管理者]: ").strip() or "管理者"
    
    # 設定保存
    users = {
        username: {
            "password_hash": generate_password_hash(password),
            "role": "admin",
            "display_name": display_name,
            "created_at": datetime.now().isoformat()
        }
    }
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    
    print("\n✅ セットアップ完了！")
    print(f"   - 管理者アカウント: {username}")
    print(f"   - 設定ファイル: {config_path}")
    print(f"   - リカバリーファイル: {recovery_path}")
    
    # .gitignore確認
    gitignore_path = os.path.join(os.path.dirname(config_path), '..', '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            content = f.read()
        if 'auth_users.json' not in content or '.recovery_key' not in content:
            print("\n⚠️  推奨: 以下のファイルを.gitignoreに追加してください:")
            print("   python/config/auth_users.json")
            print("   python/config/.recovery_key")


def verify_recovery_key(recovery_key, recovery_path):
    """リカバリーキーの検証"""
    if not os.path.exists(recovery_path):
        return False
    
    try:
        with open(recovery_path, 'r') as f:
            data = json.load(f)
        return check_password_hash(data['recovery_hash'], recovery_key)
    except:
        return False


def authenticate_admin(config_path):
    """管理者認証"""
    print("\n🔐 管理者認証が必要です")
    username = input("管理者のユーザー名: ").strip()
    password = getpass.getpass("管理者のパスワード: ")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        if username in users and users[username].get('role') == 'admin':
            if check_password_hash(users[username]['password_hash'], password):
                print("✅ 認証成功")
                return True
    except:
        pass
    
    return False


def add_new_user(config_path):
    """新規ユーザー追加"""
    print("\n👤 新規ユーザーを追加します")
    
    # 既存ユーザー読み込み
    with open(config_path, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    # ユーザー情報入力
    while True:
        username = input("新規ユーザー名: ").strip()
        if not username:
            print("❌ ユーザー名を入力してください")
            continue
        if username in users:
            print(f"❌ ユーザー '{username}' は既に存在します")
            continue
        break
    
    while True:
        password = getpass.getpass("パスワード: ")
        if len(password) < 8:
            print("❌ パスワードは8文字以上で設定してください")
            continue
        
        password_confirm = getpass.getpass("パスワード（確認）: ")
        if password != password_confirm:
            print("❌ パスワードが一致しません")
            continue
        break
    
    display_name = input(f"表示名 [{username}]: ").strip() or username
    
    print("\n📋 ロールを選択してください:")
    print("  1. admin  - 全機能にアクセス可能")
    print("  2. user   - 通常利用者（デフォルト）")
    print("  3. viewer - 閲覧のみ")
    
    role_choice = input("選択 (1-3) [2]: ").strip() or "2"
    roles = {"1": "admin", "2": "user", "3": "viewer"}
    role = roles.get(role_choice, "user")
    
    # ユーザー追加
    users[username] = {
        "password_hash": generate_password_hash(password),
        "role": role,
        "display_name": display_name,
        "created_at": datetime.now().isoformat()
    }
    
    # 保存
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ ユーザー '{username}' を追加しました")
    print(f"   - ロール: {role}")
    print(f"   - 表示名: {display_name}")


def reset_password(config_path):
    """パスワードリセット"""
    print("\n🔄 パスワードリセット")
    
    # 既存ユーザー読み込み
    with open(config_path, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    # ユーザー一覧表示
    print("\n登録ユーザー:")
    for username in users:
        print(f"  - {username} ({users[username]['role']})")
    
    # リセット対象選択
    username = input("\nリセットするユーザー名: ").strip()
    if username not in users:
        print(f"❌ ユーザー '{username}' が見つかりません")
        return
    
    # 新パスワード設定
    while True:
        password = getpass.getpass("新しいパスワード: ")
        if len(password) < 8:
            print("❌ パスワードは8文字以上で設定してください")
            continue
        
        password_confirm = getpass.getpass("新しいパスワード（確認）: ")
        if password != password_confirm:
            print("❌ パスワードが一致しません")
            continue
        break
    
    # パスワード更新
    users[username]['password_hash'] = generate_password_hash(password)
    users[username]['updated_at'] = datetime.now().isoformat()
    
    # 保存
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ ユーザー '{username}' のパスワードをリセットしました")


def list_users(config_path):
    """ユーザー一覧表示"""
    print("\n📋 登録ユーザー一覧")
    print("-" * 60)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    for username, info in users.items():
        print(f"\nユーザー名: {username}")
        print(f"  表示名: {info.get('display_name', username)}")
        print(f"  ロール: {info.get('role', 'user')}")
        print(f"  作成日: {info.get('created_at', 'N/A')}")
        if 'updated_at' in info:
            print(f"  更新日: {info['updated_at']}")
    
    print("-" * 60)
    print(f"合計: {len(users)} ユーザー")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 中断されました")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)