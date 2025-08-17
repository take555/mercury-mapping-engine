# enhanced.py のHTMLテンプレート部分に追加

def _build_enhanced_analysis_form() -> str:
    """高精度分析フォーム（モード選択付き）"""
    return """
    <div class="upload-section">
        <h2>🔥 高精度CSV分析 - Brute Force Matching</h2>
        
        <form method="post" enctype="multipart/form-data" class="analysis-form">
            <div class="file-inputs">
                <div class="file-group">
                    <label for="file_a">📄 A社CSVファイル:</label>
                    <input type="file" id="file_a" name="file_a" accept=".csv" required>
                </div>
                
                <div class="file-group">
                    <label for="file_b">📄 B社CSVファイル:</label>
                    <input type="file" id="file_b" name="file_b" accept=".csv" required>
                </div>
            </div>
            
            <!-- 🆕 分析モード選択 -->
            <div class="analysis-mode-section">
                <h3>⚙️ 分析モード選択</h3>
                <div class="mode-options">
                    <div class="mode-option">
                        <input type="radio" id="mode_library" name="similarity_mode" value="library" checked>
                        <label for="mode_library" class="mode-label">
                            <div class="mode-header">
                                <span class="mode-icon">🐍</span>
                                <strong>Library Mode</strong>
                                <span class="mode-badge free">無料</span>
                            </div>
                            <div class="mode-description">
                                <p>Python ライブラリベースの高速分析</p>
                                <ul>
                                    <li>✅ 高速処理（数秒〜数分）</li>
                                    <li>✅ 無制限使用</li>
                                    <li>✅ 文字列・数値類似度</li>
                                    <li>⚡ おすすめ: 初回分析・大量処理</li>
                                </ul>
                            </div>
                        </label>
                    </div>
                    
                    <div class="mode-option">
                        <input type="radio" id="mode_ai" name="similarity_mode" value="ai">
                        <label for="mode_ai" class="mode-label">
                            <div class="mode-header">
                                <span class="mode-icon">🤖</span>
                                <strong>AI Mode</strong>
                                <span class="mode-badge premium">Premium</span>
                            </div>
                            <div class="mode-description">
                                <p>Claude AI による意味理解分析</p>
                                <ul>
                                    <li>✅ 意味的類似度判定</li>
                                    <li>✅ 文脈・ビジネスロジック理解</li>
                                    <li>✅ 多言語対応（英⇔日）</li>
                                    <li>💰 API使用料: ~$0.01-0.05</li>
                                    <li>🎯 おすすめ: 高精度が必要な場合</li>
                                </ul>
                            </div>
                        </label>
                    </div>
                </div>
            </div>
            
            <!-- 詳細設定 -->
            <div class="advanced-settings">
                <h3>🔧 詳細設定</h3>
                <div class="settings-grid">
                    <div class="setting-item">
                        <label for="sample_size">サンプルサイズ:</label>
                        <select id="sample_size" name="max_sample_size">
                            <option value="50">50行 (高速テスト)</option>
                            <option value="100" selected>100行 (推奨)</option>
                            <option value="200">200行 (詳細分析)</option>
                            <option value="500">500行 (完全分析)</option>
                        </select>
                    </div>
                    
                    <div class="setting-item">
                        <label for="full_analysis">
                            <input type="checkbox" id="full_analysis" name="full_analysis" checked>
                            フル分析実行
                        </label>
                    </div>
                    
                    <div class="setting-item ai-only" style="display: none;">
                        <label for="ai_model">AIモデル:</label>
                        <select id="ai_model" name="ai_model">
                            <option value="claude-3-haiku-20240307">Haiku (高速・低コスト)</option>
                            <option value="claude-3-sonnet-20240229">Sonnet (バランス)</option>
                            <option value="claude-3-5-sonnet-20240620">3.5 Sonnet (高性能)</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="submit-section">
                <button type="submit" class="btn-analyze">
                    <span class="btn-icon">🚀</span>
                    <span class="btn-text">分析開始</span>
                </button>
                <div class="analysis-info">
                    <p class="info-text">選択されたモードで高精度分析を実行します</p>
                </div>
            </div>
        </form>
    </div>
    
    <style>
    .analysis-mode-section {
        margin: 20px 0;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 8px;
    }
    
    .mode-options {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-top: 15px;
    }
    
    .mode-option {
        position: relative;
    }
    
    .mode-option input[type="radio"] {
        position: absolute;
        opacity: 0;
        width: 0;
        height: 0;
    }
    
    .mode-label {
        display: block;
        padding: 15px;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        background: white;
    }
    
    .mode-option input[type="radio"]:checked + .mode-label {
        border-color: #007bff;
        background: #f0f8ff;
        box-shadow: 0 2px 8px rgba(0,123,255,0.1);
    }
    
    .mode-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
    }
    
    .mode-icon {
        font-size: 1.2em;
    }
    
    .mode-badge {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        margin-left: auto;
    }
    
    .mode-badge.free {
        background: #d4edda;
        color: #155724;
    }
    
    .mode-badge.premium {
        background: #fff3cd;
        color: #856404;
    }
    
    .mode-description ul {
        margin: 8px 0;
        padding-left: 15px;
        font-size: 0.9em;
    }
    
    .mode-description li {
        margin: 3px 0;
    }
    
    .advanced-settings {
        margin: 20px 0;
        padding: 15px;
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
    
    .settings-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }
    
    .setting-item label {
        display: block;
        margin-bottom: 5px;
        font-weight: 500;
    }
    
    .setting-item select {
        width: 100%;
        padding: 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    
    .ai-only {
        opacity: 0.5;
        transition: opacity 0.3s ease;
    }
    
    .submit-section {
        text-align: center;
        margin-top: 30px;
    }
    
    .btn-analyze {
        background: linear-gradient(135deg, #007bff, #0056b3);
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 6px;
        font-size: 1.1em;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        transition: all 0.3s ease;
    }
    
    .btn-analyze:hover {
        background: linear-gradient(135deg, #0056b3, #003d82);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,123,255,0.3);
    }
    
    .analysis-info {
        margin-top: 15px;
        color: #666;
        font-size: 0.9em;
    }
    </style>
    
    <script>
    // モード切り替え時の動的UI更新
    document.addEventListener('DOMContentLoaded', function() {
        const libraryMode = document.getElementById('mode_library');
        const aiMode = document.getElementById('mode_ai');
        const aiOnlySettings = document.querySelectorAll('.ai-only');
        const analysisInfo = document.querySelector('.info-text');
        
        function updateUI() {
            if (aiMode.checked) {
                aiOnlySettings.forEach(el => {
                    el.style.display = 'block';
                    el.style.opacity = '1';
                });
                analysisInfo.textContent = 'Claude AIによる高精度意味解析を実行します（API使用料が発生します）';
            } else {
                aiOnlySettings.forEach(el => {
                    el.style.display = 'none';
                    el.style.opacity = '0.5';
                });
                analysisInfo.textContent = 'Pythonライブラリによる高速分析を実行します（無料）';
            }
        }
        
        libraryMode.addEventListener('change', updateUI);
        aiMode.addEventListener('change', updateUI);
        updateUI(); // 初期化
    });
    </script>
    """