"""
Основное FastAPI приложение для AI Visibility MVP - адаптированное для Vercel
"""

import os
import tempfile
import threading
import hashlib
from typing import Optional
import pandas as pd
from io import BytesIO

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from starlette.middleware.cors import CORSMiddleware

# Импорт наших модулей
from config import EMAIL_REGEX, MAX_UPLOAD_MB, ALLOW_RETRY_SAME_FILE, validate_config
from database import db
from file_processor import FileProcessor
from openai_client import openai_client
from metrics import MetricsCalculator
from email_service import email_service

# Создание FastAPI приложения
app = FastAPI(
    title="AI Visibility MVP",
    description="Сервис для анализа видимости в ChatGPT",
    version="1.0.0"
)

# Добавление CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# HTML лендинг страницы встроенный в код
LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Visibility Analytics - Analyze Your Brand's AI Search Presence</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 3rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 1rem;
            font-size: 2.5rem;
            font-weight: 700;
        }
        
        .subtitle {
            text-align: center;
            color: #7f8c8d;
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .feature {
            text-align: center;
            padding: 1.5rem;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .feature h3 {
            color: #2c3e50;
            margin-bottom: 0.5rem;
        }
        
        .upload-section {
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #2c3e50;
            font-weight: 600;
        }
        
        input[type="email"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        input[type="email"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .file-upload {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        
        input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 2px dashed #ddd;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: border-color 0.3s;
        }
        
        input[type="file"]:hover {
            border-color: #667eea;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
            margin-left: 1rem;
        }
        
        .btn-secondary:hover {
            background: #5a6268;
            transform: translateY(-2px);
        }
        
        .template-section {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .format-info {
            background: #e3f2fd;
            padding: 1.5rem;
            border-radius: 10px;
            margin-top: 2rem;
        }
        
        .format-info h4 {
            color: #1976d2;
            margin-bottom: 1rem;
        }
        
        .format-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        .format-table th,
        .format-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .format-table th {
            background: #f5f5f5;
            font-weight: 600;
        }
        
        .status {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 8px;
            display: none;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 2rem;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            .card {
                padding: 2rem;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .btn-secondary {
                margin-left: 0;
                margin-top: 1rem;
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🤖 AI Visibility Analytics</h1>
            <p class="subtitle">Analyze your brand's visibility in ChatGPT, Claude, and other AI search engines</p>
            
            <div class="feature-grid">
                <div class="feature">
                    <div class="feature-icon">📊</div>
                    <h3>AIV Score</h3>
                    <p>Get your AI Visibility Score from 0-100 with detailed metrics</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🌍</div>
                    <h3>Geo-Targeting</h3>
                    <p>Analyze visibility across different countries and languages</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🏆</div>
                    <h3>Competitor Analysis</h3>
                    <p>See how you rank against competitors in AI search results</p>
                </div>
            </div>
            
            <div class="template-section">
                <h3>📋 Start with Our Template</h3>
                <p>Download our CSV template with examples to get started quickly</p>
                <a href="/download-template" class="btn btn-secondary" download>
                    📥 Download Template
                </a>
            </div>
            
            <div class="upload-section">
                <h3>🚀 Upload Your Analysis File</h3>
                <form id="uploadForm">
                    <div class="form-group">
                        <label for="email">Email Address (for receiving results)</label>
                        <input type="email" id="email" name="email" required placeholder="your.email@company.com">
                    </div>
                    
                    <div class="form-group">
                        <label for="file">Upload CSV/Excel File</label>
                        <input type="file" id="file" name="file" accept=".csv,.xlsx,.tsv" required>
                        <small style="color: #666; margin-top: 0.5rem; display: block;">
                            Supported formats: CSV, XLSX, TSV (Max 10MB)
                        </small>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">
                        🔍 Analyze AI Visibility
                    </button>
                </form>
                
                <div id="status" class="status"></div>
            </div>
            
            <div class="format-info">
                <h4>📋 Required File Format</h4>
                <p>Your CSV file must contain exactly these 3 columns:</p>
                <table class="format-table">
                    <thead>
                        <tr>
                            <th>Column</th>
                            <th>Description</th>
                            <th>Example</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Country</strong></td>
                            <td>Target country for geo-specific analysis</td>
                            <td>USA, UK, Germany</td>
                        </tr>
                        <tr>
                            <td><strong>Prompt</strong></td>
                            <td>Search query to analyze</td>
                            <td>"best vacuum cleaner 2024"</td>
                        </tr>
                        <tr>
                            <td><strong>Website</strong></td>
                            <td>Your domain to track</td>
                            <td>amazon.com</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>&copy; 2024 AI Visibility Analytics. Powered by OpenAI & Advanced Analytics.</p>
        </div>
    </div>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const statusDiv = document.getElementById('status');
            const submitBtn = e.target.querySelector('button[type="submit"]');
            
            // Reset status
            statusDiv.style.display = 'none';
            statusDiv.className = 'status';
            
            // Disable submit button
            submitBtn.disabled = true;
            submitBtn.innerHTML = '⏳ Processing...';
            
            // Get form data
            const formData = new FormData();
            formData.append('email', document.getElementById('email').value);
            formData.append('file', document.getElementById('file').files[0]);
            
            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = `
                        <strong>✅ Success!</strong><br>
                        Your file has been received and is being processed.<br>
                        Results will be sent to <strong>${result.email}</strong> within 5-10 minutes.
                    `;
                    
                    // Reset form
                    document.getElementById('uploadForm').reset();
                } else {
                    throw new Error(result.detail || 'Upload failed');
                }
            } catch (error) {
                statusDiv.className = 'status error';
                statusDiv.innerHTML = `
                    <strong>❌ Error:</strong><br>
                    ${error.message}
                `;
            } finally {
                // Re-enable submit button
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🔍 Analyze AI Visibility';
                statusDiv.style.display = 'block';
            }
        });
        
        // File validation
        document.getElementById('file').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const maxSize = 10 * 1024 * 1024; // 10MB
                if (file.size > maxSize) {
                    alert('File too large. Maximum size is 10MB.');
                    e.target.value = '';
                    return;
                }
                
                const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
                if (!validTypes.includes(file.type) && !file.name.match(/\\.(csv|xlsx|tsv)$/i)) {
                    alert('Invalid file type. Please upload CSV, XLSX, or TSV files only.');
                    e.target.value = '';
                    return;
                }
            }
        });
    </script>
</body>
</html>"""

def get_client_ip(request: Request) -> str:
    """Получение IP адреса клиента"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "0.0.0.0"

def create_geo_targeted_prompt(prompt: str, country: str) -> str:
    """
    Создание геотаргетированного промпта для OpenAI
    
    Args:
        prompt: Исходный запрос
        country: Страна для таргетинга
        
    Returns:
        Модифицированный запрос с геотаргетингом
    """
    country_prompts = {
        'USA': 'Answer as if responding to someone in the United States',
        'UK': 'Answer as if responding to someone in the United Kingdom', 
        'Germany': 'Answer as if responding to someone in Germany, auf Deutsch wenn nötig',
        'France': 'Answer as if responding to someone in France, en français si nécessaire',
        'Canada': 'Answer as if responding to someone in Canada',
        'Australia': 'Answer as if responding to someone in Australia'
    }
    
    geo_context = country_prompts.get(country, f'Answer as if responding to someone in {country}')
    return f"{geo_context}: {prompt}"

def create_template_csv() -> bytes:
    """
    Создание CSV шаблона в памяти
    
    Returns:
        Bytes содержимого CSV файла
    """
    template_data = {
        'Country': [
            'UK', 'USA', 'Germany', 'UK', 'USA'
        ],
        'Prompt': [
            'Dyson V15 cordless vacuum cleaner best price',
            'KitchenAid stand mixer reviews USA', 
            'Samsung Waschmaschine 9kg Frontlader',
            'Ninja air fryer large capacity reviews',
            'Bosch dishwasher built-in stainless steel'
        ],
        'Website': [
            'amazon.com', 'amazon.com', 'amazon.com', 'amazon.com', 'amazon.com'
        ]
    }
    
    df = pd.DataFrame(template_data)
    
    # Создаем CSV в памяти
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    
    return output.getvalue()

def process_file_worker(file_path: str, email: str, ip: str) -> None:
    """
    Worker функция для асинхронной обработки файла
    
    Args:
        file_path: Путь к временному файлу
        email: Email пользователя  
        ip: IP адрес пользователя
    """
    try:
        # Обработка файла
        queries_df, processed_count = FileProcessor.process_file(file_path)
        
        # Создание списка для результатов
        results = []
        
        # Обработка каждого запроса
        for _, row in queries_df.iterrows():
            country = row['Country']
            prompt = row['Prompt']
            target_domain = row['target_domain']
            
            # Создание геотаргетированного запроса
            geo_prompt = create_geo_targeted_prompt(prompt, country)
            
            # Вызов OpenAI API
            search_result = openai_client.search_with_web(geo_prompt)
            sources = search_result["sources"]
            usage = search_result["usage"]
            
            # Расчет метрик для конкретного домена
            metrics = MetricsCalculator.calculate_metrics_for_query(
                sources, target_domain, country
            )
            
            # Добавление базовых данных
            result_row = {
                "Оригинальный промпт": prompt,
                "Геотаргетированный промпт": geo_prompt,
                **metrics,
                "Tokens Used": getattr(usage, "total_tokens", None) if usage else None
            }
            
            results.append(result_row)
        
        # Создание DataFrame и CSV
        results_df = pd.DataFrame(results)
        csv_content = results_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        
        # Сохранение email в базу
        db.save_email(email, ip)
        
        # Отправка отчета
        email_service.send_report_email(email, csv_content, len(results))
        
    except Exception as e:
        print(f"Ошибка обработки файла: {e}")
    finally:
        # Удаление временного файла
        try:
            os.remove(file_path)
        except:
            pass

# Vercel serverless function initialization
@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    try:
        # В Vercel serverless окружении не все конфигурации могут быть доступны
        # validate_config()  # Комментируем для Vercel
        print("✅ AI Visibility MVP запущен на Vercel")
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        # В serverless среде не останавливаем приложение
        pass

@app.get("/")
async def serve_landing():
    """Отдача лендинг страницы"""
    return HTMLResponse(content=LANDING_HTML, status_code=200)

@app.get("/download-template")
async def download_template():
    """
    Эндпоинт для скачивания шаблона CSV файла
    
    Returns:
        CSV файл с примерами
    """
    csv_bytes = create_template_csv()
    
    return StreamingResponse(
        BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ai_visibility_template.csv"}
    )

@app.post("/submit")
async def submit_file(
    request: Request,
    email: str = Form(..., description="Email для отправки отчета"),
    file: UploadFile = File(..., description="Файл с промптами (CSV/TSV/XLSX)")
):
    """
    Эндпоинт для загрузки файла и запуска обработки
    
    Args:
        request: HTTP запрос
        email: Email пользователя
        file: Загружаемый файл
        
    Returns:
        JSON ответ с статусом обработки
    """
    # Валидация email
    if not EMAIL_REGEX.match(email):
        raise HTTPException(status_code=400, detail="Неверный формат email")
    
    # Чтение содержимого файла
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Ошибка чтения файла")
    
    # Проверка размера файла
    try:
        FileProcessor.validate_file_size(content, MAX_UPLOAD_MB)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Получение IP и хеша файла
    client_ip = get_client_ip(request)
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Проверка IP и файла (упрощенная для Vercel)
    try:
        db.check_ip_file_access(client_ip, file_hash, ALLOW_RETRY_SAME_FILE)
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        # В serverless среде могут быть проблемы с базой данных
        print(f"Database warning: {e}")
        pass
    
    # Сохранение файла во временную директорию
    file_extension = FileProcessor.get_file_extension(file.filename)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка сохранения файла")
    
    # Запуск асинхронной обработки
    worker_thread = threading.Thread(
        target=process_file_worker,
        args=(temp_file_path, email, client_ip),
        daemon=True
    )
    worker_thread.start()
    
    # Возврат успешного ответа
    return JSONResponse({
        "ok": True,
        "email": email,
        "status": "processing",
        "message": "Файл принят в обработку. Ожидайте отчет на email."
    })

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "ok", "service": "AI Visibility MVP", "platform": "Vercel"}

@app.get("/api")
async def api_info():
    """Информация об API"""
    return {
        "message": "AI Visibility MVP API", 
        "version": "1.0.0",
        "platform": "Vercel Serverless",
        "supported_format": "CSV with columns: Country, Prompt, Website",
        "template_download": "/download-template",
        "endpoints": ["/submit", "/download-template", "/health"]
    }

# Vercel serverless handler
def handler(request, response):
    """Vercel serverless handler"""
    return app(request, response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)