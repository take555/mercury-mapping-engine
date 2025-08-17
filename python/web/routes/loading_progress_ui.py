# enhanced.py の _build_enhanced_analysis_form() 内のJavaScriptとCSSを拡張

def _build_enhanced_analysis_form() -> str:
    """高精度分析フォーム（プログレス表示付き）"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔥 高精度CSV分析 - Mercury Mapping Engine</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            .header { background: linear-gradient(135deg, #2196F3, #1976D2); color: white; padding: 25px; border-radius: 8px; margin-bottom: 30px; text-align: center; }
            .header h1 { margin: 0; font-size: 2em; }
            .header p { margin: 10px 0 0 0; opacity: 0.9; }
            
            .file-inputs { margin: 25px 0; }
            .file-group { margin: 15px 0; }
            .file-group label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
            .file-group input[type="file"] { width: 100%; padding: 12px; border: 2px dashed #ccc; border-radius: 6px; background: #fafafa; transition: border-color 0.3s; }
            .file-group input[type="file"]:hover { border-color: #2196F3; }
            
            .analysis-mode-section { margin: 25px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .mode-options { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
            .mode-option { position: relative; }
            .mode-option input[type="radio"] { position: absolute; opacity: 0; width: 0; height: 0; }
            
            .mode-label { display: block; padding: 20px; border: 2px solid #e0e0e0; border-radius: 10px; cursor: pointer; transition: all 0.3s ease; background: white; }
            .mode-option input[type="radio"]:checked + .mode-label { border-color: #2196F3; background: #f0f8ff; box-shadow: 0 4px 12px rgba(33,150,243,0.15); }
            
            .mode-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
            .mode-icon { font-size: 1.4em; }
            .mode-badge { padding: 4px 10px; border-radius: 15px; font-size: 0.8em; font-weight: bold; margin-left: auto; }
            .mode-badge.free { background: #d4edda; color: #155724; }
            .mode-badge.premium { background: #fff3cd; color: #856404; }
            
            .mode-description ul { margin: 10px 0; padding-left: 20px; font-size: 0.9em; color: #555; }
            .mode-description li { margin: 5px 0; }
            
            .advanced-settings { margin: 25px 0; padding: 20px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; }
            .settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 15px; }
            .setting-item label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
            .setting-item select, .setting-item input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; }
            
            .ai-only { opacity: 0.5; transition: opacity 0.3s ease; }
            
            .submit-section { text-align: center; margin-top: 35px; position: relative; }
            .btn-analyze { 
                background: linear-gradient(135deg, #2196F3, #1976D2); 
                color: white; border: none; padding: 15px 40px; border-radius: 8px; 
                font-size: 1.2em; cursor: pointer; display: inline-flex; 
                align-items: center; gap: 10px; transition: all 0.3s ease; 
                box-shadow: 0 4px 12px rgba(33,150,243,0.3);
                position: relative;
            }
            .btn-analyze:hover:not(:disabled) { 
                background: linear-gradient(135deg, #1976D2, #1565C0); 
                transform: translateY(-2px); 
                box-shadow: 0 6px 16px rgba(33,150,243,0.4); 
            }
            .btn-analyze:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            /* ローディング表示 */
            .loading-overlay {
                display: none;
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.7);
                z-index: 9999;
                align-items: center;
                justify-content: center;
            }
            
            .loading-container {
                background: white;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                max-width: 500px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            
            .loading-spinner {
                width: 60px;
                height: 60px;
                border: 4px solid #e0e0e0;
                border-left: 4px solid #2196F3;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .progress-container {
                margin: 20px 0;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                overflow: hidden;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #2196F3, #21CBF3);
                width: 0%;
                transition: width 0.3s ease;
                animation: progress-shimmer 2s infinite;
            }
            
            @keyframes progress-shimmer {
                0% { background-position: -200px 0; }
                100% { background-position: 200px 0; }
            }
            
            .loading-steps {
                text-align: left;
                margin: 20px 0;
            }
            
            .loading-step {
                padding: 8px 0;
                display: flex;
                align-items: center;
                gap: 10px;
                opacity: 0.5;
                transition: opacity 0.3s ease;
            }
            
            .loading-step.active {
                opacity: 1;
                color: #2196F3;
                font-weight: 500;
            }
            
            .loading-step.completed {
                opacity: 0.7;
                color: #4CAF50;
            }
            
            .step-icon {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: #e0e0e0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
            }
            
            .loading-step.active .step-icon {
                background: #2196F3;
                color: white;
                animation: pulse 1.5s infinite;
            }
            
            .loading-step.completed .step-icon {
                background: #4CAF50;
                color: white;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            
            .estimated-time {
                margin: 15px 0;
                padding: 12px;
                background: #f0f8ff;
                border-radius: 6px;
                font-size: 0.9em;
                color: #1976D2;
            }
            
            .cancel-btn {
                background: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 15px;
            }
            
            .analysis-info { margin-top: 20px; color: #666; font-size: 0.9em; }
            .nav-links { margin-top: 30px; text-align: center; }
            .nav-links a { margin: 0 10px; padding: 8px 16px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔥 高精度CSV分析</h1>
                <p>Mercury Mapping Engine v2.0 - Brute Force Matching</p>
            </div>
            
            <form method="post" enctype="multipart/form-data" class="analysis-form" id="analysisForm">
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
                
                <div class="advanced-settings">
                    <h3>🔧 詳細設定</h3>
                    <div class="settings-grid">
                        <div class="setting-item">
                            <label for="sample_size">サンプルサイズ:</label>
                            <select id="sample_size" name="max_sample_size">
                                <option value="20">20行 (超高速テスト)</option>
                                <option value="50">50行 (高速テスト)</option>
                                <option value="100" selected>100行 (推奨)</option>
                                <option value="200">200行 (詳細分析)</option>
                            </select>
                        </div>
                        
                        <div class="setting-item">
                            <label>
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
                    <button type="submit" class="btn-analyze" id="analyzeBtn">
                        <span class="btn-icon">🚀</span>
                        <span class="btn-text">分析開始</span>
                    </button>
                    <div class="analysis-info">
                        <p class="info-text">選択されたモードで高精度分析を実行します</p>
                    </div>
                </div>
            </form>
            
            <div class="nav-links">
                <a href="/">🏠 トップページ</a>
                <a href="/test/claude">🤖 Claude接続テスト</a>
                <a href="/test/models">📊 モデル一覧</a>
                <a href="/api/health">💚 システム状態</a>
            </div>
        </div>
        
        <!-- ローディングオーバーレイ -->
        <div class="loading-overlay" id="loadingOverlay">
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <h3 id="loadingTitle">🔥 分析実行中...</h3>
                
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                </div>
                
                <div class="estimated-time" id="estimatedTime">
                    推定残り時間: 計算中...
                </div>
                
                <div class="loading-steps">
                    <div class="loading-step active" id="step1">
                        <div class="step-icon">1</div>
                        <span>ファイルアップロード</span>
                    </div>
                    <div class="loading-step" id="step2">
                        <div class="step-icon">2</div>
                        <span>CSV構造解析</span>
                    </div>
                    <div class="loading-step" id="step3">
                        <div class="step-icon">3</div>
                        <span id="step3Text">力技マッチング実行</span>
                    </div>
                    <div class="loading-step" id="step4">
                        <div class="step-icon">4</div>
                        <span>フィールドマッピング分析</span>
                    </div>
                    <div class="loading-step" id="step5">
                        <div class="step-icon">5</div>
                        <span>結果統合・表示</span>
                    </div>
                </div>
                
                <div style="margin-top: 20px; font-size: 0.9em; color: #666;">
                    <p id="processingNote">データを分析中です。しばらくお待ちください...</p>
                </div>
            </div>
        </div>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const libraryMode = document.getElementById('mode_library');
            const aiMode = document.getElementById('mode_ai');
            const aiOnlySettings = document.querySelectorAll('.ai-only');
            const analysisInfo = document.querySelector('.info-text');
            const form = document.getElementById('analysisForm');
            const analyzeBtn = document.getElementById('analyzeBtn');
            const loadingOverlay = document.getElementById('loadingOverlay');
            
            let currentStep = 1;
            let startTime;
            
            function updateUI() {
                if (aiMode.checked) {
                    aiOnlySettings.forEach(el => {
                        el.style.display = 'block';
                        el.style.opacity = '1';
                    });
                    analysisInfo.textContent = 'Claude AIによる高精度意味解析を実行します（API使用料が発生します）';
                    document.getElementById('step3Text').textContent = 'AI意味解析実行';
                } else {
                    aiOnlySettings.forEach(el => {
                        el.style.display = 'none';
                        el.style.opacity = '0.5';
                    });
                    analysisInfo.textContent = 'Pythonライブラリによる高速分析を実行します（無料）';
                    document.getElementById('step3Text').textContent = '力技マッチング実行';
                }
            }
            
            function showLoading() {
                loadingOverlay.style.display = 'flex';
                analyzeBtn.disabled = true;
                startTime = Date.now();
                
                // プログレス更新開始
                simulateProgress();
                
                // ステップ更新開始
                setTimeout(() => updateStep(2), 1000);
                setTimeout(() => updateStep(3), 3000);
                setTimeout(() => updateStep(4), aiMode.checked ? 15000 : 8000);
                setTimeout(() => updateStep(5), aiMode.checked ? 25000 : 12000);
            }
            
            function updateStep(step) {
                // 前のステップを完了状態に
                if (currentStep > 1) {
                    const prevStep = document.getElementById(`step${currentStep}`);
                    prevStep.classList.remove('active');
                    prevStep.classList.add('completed');
                    prevStep.querySelector('.step-icon').textContent = '✓';
                }
                
                // 現在のステップをアクティブに
                if (step <= 5) {
                    const currentStepEl = document.getElementById(`step${step}`);
                    currentStepEl.classList.add('active');
                    currentStep = step;
                }
            }
            
            function simulateProgress() {
                const progressFill = document.getElementById('progressFill');
                const estimatedTime = document.getElementById('estimatedTime');
                const processingNote = document.getElementById('processingNote');
                
                let progress = 0;
                const isAI = aiMode.checked;
                const totalTime = isAI ? 30000 : 15000; // AIモード: 30秒, ライブラリモード: 15秒
                const interval = 200;
                
                const progressInterval = setInterval(() => {
                    const elapsed = Date.now() - startTime;
                    progress = Math.min((elapsed / totalTime) * 100, 95); // 95%まで
                    
                    progressFill.style.width = progress + '%';
                    
                    const remainingTime = Math.max(0, totalTime - elapsed);
                    const remainingSeconds = Math.ceil(remainingTime / 1000);
                    
                    if (remainingSeconds > 0) {
                        estimatedTime.textContent = `推定残り時間: ${remainingSeconds}秒`;
                    } else {
                        estimatedTime.textContent = '最終処理中...';
                    }
                    
                    // ステップ別メッセージ
                    const messages = [
                        'ファイルをアップロード中...',
                        'CSVファイルを解析中...',
                        isAI ? 'Claude AIで意味解析中...' : '力技マッチング実行中...',
                        'フィールドマッピングを生成中...',
                        '結果を統合中...'
                    ];
                    
                    if (currentStep <= messages.length) {
                        processingNote.textContent = messages[currentStep - 1];
                    }
                    
                    if (progress >= 95) {
                        clearInterval(progressInterval);
                    }
                }, interval);
            }
            
            // フォーム送信時にローディング表示
            form.addEventListener('submit', function(e) {
                // バリデーション
                const fileA = document.getElementById('file_a').files[0];
                const fileB = document.getElementById('file_b').files[0];
                
                if (!fileA || !fileB) {
                    alert('両方のCSVファイルを選択してください');
                    e.preventDefault();
                    return;
                }
                
                // ローディング表示
                showLoading();
                
                // AIモードの場合は警告
                if (aiMode.checked) {
                    document.getElementById('loadingTitle').textContent = '🤖 AI分析実行中...';
                    document.getElementById('processingNote').textContent = 'Claude AIが意味解析を実行中です。高精度な結果をお待ちください...';
                } else {
                    document.getElementById('loadingTitle').textContent = '🐍 高速分析実行中...';
                }
            });
            
            libraryMode.addEventListener('change', updateUI);
            aiMode.addEventListener('change', updateUI);
            updateUI();
        });
        </script>
    </body>
    </html>
    """