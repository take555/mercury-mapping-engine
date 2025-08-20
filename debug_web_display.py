#!/usr/bin/env python3
"""
Webアプリの表示問題をデバッグ
"""

import sys
import requests

def test_web_display():
    print("=" * 60)
    print("🔍 Webアプリ表示デバッグ")
    print("=" * 60)
    
    url = "http://localhost:5001/test/files/enhanced"
    
    # ファイル設定
    files = {
        'file_a': open('/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Youyadatasample.csv', 'rb'),
        'file_b': open('/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Tay2datasample.csv', 'rb')
    }
    
    data = {
        'similarity_mode': 'library',
        'max_sample_size': '100'
    }
    
    print("📤 リクエスト送信中...")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=60)
        
        print(f"📊 レスポンス情報:")
        print(f"   ステータスコード: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {len(response.text):,} bytes")
        
        if response.status_code == 200:
            html = response.text
            
            # マッチ数の確認
            import re
            match_count_pattern = r"マッチしたカード数:</strong>\s*(\d+)件"
            table_count_pattern = r"同一カード対応表（(\d+)件）"
            
            match_count = re.search(match_count_pattern, html)
            table_count = re.search(table_count_pattern, html)
            
            print(f"\n🔍 検出結果:")
            if match_count:
                print(f"   マッチしたカード数: {match_count.group(1)}件")
            else:
                print(f"   マッチしたカード数: 検出できず")
                
            if table_count:
                print(f"   テーブル表示件数: {table_count.group(1)}件")
            else:
                print(f"   テーブル表示件数: 検出できず")
            
            # テーブル行数を確認
            table_rows = html.count('<tr>') - 1  # ヘッダー行を除く
            print(f"   実際のテーブル行数: {table_rows}行")
            
            # データ行のサンプルを確認
            print(f"\n📋 テーブル内容サンプル:")
            start_table = html.find('<h3>🎯 同一カード対応表')
            if start_table != -1:
                table_section = html[start_table:start_table+3000]
                
                # No.1-3の行を抽出
                rows = []
                for i in range(1, 4):
                    row_pattern = rf'<td>{i}</td>'
                    row_start = table_section.find(row_pattern)
                    if row_start != -1:
                        row_end = table_section.find('</tr>', row_start)
                        if row_end != -1:
                            row_content = table_section[row_start:row_end]
                            # HTMLタグを除去
                            import re
                            clean_row = re.sub(r'<[^>]+>', ' ', row_content)
                            clean_row = re.sub(r'\s+', ' ', clean_row).strip()
                            rows.append(f"   行{i}: {clean_row[:100]}...")
                
                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("   データ行が見つかりません")
            else:
                print("   同一カード対応表が見つかりません")
        else:
            print(f"❌ エラー: {response.status_code}")
            print(f"レスポンス: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")
    
    finally:
        files['file_a'].close()
        files['file_b'].close()

if __name__ == "__main__":
    test_web_display()