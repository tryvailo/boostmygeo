"""
Основное FastAPI приложение для AI Visibility MVP
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
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BoostMyGEO - Перевірте, чи рекомендує ШІ ваші продукти</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-text {
            background: linear-gradient(45deg, #2563eb, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .gradient-button {
            background: linear-gradient(45deg, #059669, #10b981);
        }
        .gradient-button-blue {
            background: linear-gradient(45deg, #2563eb, #3b82f6);
        }
        .fade-in {
            animation: fadeIn 0.8s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .hover-lift {
            transition: all 0.3s ease;
        }
        .hover-lift:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        .footer {
            margin-top: 1rem;
            padding-top: 2rem;
            padding-bottom: 2rem;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body class="bg-gray-900 text-gray-200 font-sans leading-relaxed">

    <!-- Header Section -->
    <header class="py-6 px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center max-w-7xl mx-auto">
            <div class="text-2xl font-bold gradient-text">BoostMyGEO</div>
            <nav class="hidden md:flex space-x-6">
                <a href="#" class="hover:text-white transition-colors duration-200">Переваги</a>
                <a href="#" class="hover:text-white transition-colors duration-200">Як це працює</a>
                <a href="#" class="hover:text-white transition-colors duration-200">Кейси</a>
                <a href="#" class="hover:text-white transition-colors duration-200">Ціни</a>
            </nav>
            <a href="#cta" class="py-2 px-6 rounded-full text-white font-semibold shadow-lg gradient-button-blue hover-lift">
                Спробувати безкоштовно
            </a>
            <button class="md:hidden text-2xl">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-8 h-8">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path>
                </svg>
            </button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Hero Section -->
        <section class="text-center py-20 md:py-32">
            <h1 class="text-4xl md:text-6xl font-extrabold mb-4 leading-tight">
                Перевірте, чи рекомендує <span class="gradient-text">ШІ</span> ваші продукти
            </h1>
            <p class="text-lg md:text-xl text-gray-400 mb-8 max-w-3xl mx-auto">
                Отримайте оцінку видимості та проаналізуйте, як ваш бренд, товари та послуги представлені в результатах пошуку ChatGPT, Gemini, Copilot та інших.
            </p>
            <div class="space-x-4">
                <a href="#cta" class="py-3 px-8 rounded-full text-white font-bold shadow-xl hover-lift inline-block gradient-button">
                    Отримати аналіз
                </a>
            </div>
        </section>

        <!-- Features Section -->
        <section id="features" class="py-16">
            <div class="grid md:grid-cols-3 gap-8">
                <div class="bg-gray-800 p-8 rounded-2xl text-center hover-lift fade-in feature-card">
                    <div class="text-4xl mb-4">🏆</div>
                    <h3 class="text-2xl font-bold text-white mb-2">Оцінка видимості ШІ</h3>
                    <p class="text-gray-400">
                        Розраховуємо ваш AIV-Score від 0 до 100, враховуючи позицію, згадки, конкурентів та інші фактори.
                    </p>
                </div>
                <div class="bg-gray-800 p-8 rounded-2xl text-center hover-lift fade-in feature-card" style="animation-delay: 0.1s;">
                    <div class="text-4xl mb-4">🌍</div>
                    <h3 class="text-2xl font-bold text-white mb-2">Геотаргетинг</h3>
                    <p class="text-gray-400">
                        Аналізуємо результати в різних країнах та мовах, щоб оцінити вашу локальну присутність.
                    </p>
                </div>
                <div class="bg-gray-800 p-8 rounded-2xl text-center hover-lift fade-in feature-card" style="animation-delay: 0.2s;">
                    <div class="text-4xl mb-4">📈</div>
                    <h3 class="text-2xl font-bold text-white mb-2">Звіт з деталями</h3>
                    <p class="text-gray-400">
                        Надсилаємо повний звіт про видимість вашого бренду в ШІ-пошуку з ключовими показниками.
                    </p>
                </div>
            </div>
        </section>
        
        <!-- How It Works Section -->
        <section id="how-it-works" class="py-16">
            <h2 class="text-3xl md:text-4xl font-bold text-center mb-12">
                Як це працює
            </h2>
            <div class="grid md:grid-cols-2 gap-12 items-center">
                <div class="space-y-6">
                    <div class="p-6 bg-gray-800 rounded-xl hover-lift">
                        <h4 class="text-xl font-semibold mb-2 text-white">1. Завантажте файл</h4>
                        <p class="text-gray-400">
                            Просто завантажте файл CSV або XLSX із переліком продуктів, ключових запитів і доменів.
                        </p>
                        <a href="/api/download-template" class="text-blue-400 hover:text-blue-300 transition-colors duration-200 mt-2 block font-medium" download>
                            Завантажити шаблон →
                        </a>
                    </div>
                    <div class="p-6 bg-gray-800 rounded-xl hover-lift">
                        <h4 class="text-xl font-semibold mb-2 text-white">2. ШІ аналізує дані</h4>
                        <p class="text-gray-400">
                            Наш алгоритм на основі передових ШІ-моделей аналізує, як ваш бренд, продукти та послуги представлені в ШІ-пошуку.
                        </p>
                    </div>
                    <div class="p-6 bg-gray-800 rounded-xl hover-lift">
                        <h4 class="text-xl font-semibold mb-2 text-white">3. Отримайте звіт</h4>
                        <p class="text-gray-400">
                            Ми надішлемо вам детальний звіт на електронну пошту з вашим AIV-Score та рекомендаціями.
                        </p>
                    </div>
                </div>
                <div>
                    <img src="https://placehold.co/400x300/1e293b/d1d5db?text=AI+Analysis" alt="AI analysis process illustration" class="w-full h-auto rounded-xl shadow-lg">
                </div>
            </div>
        </section>

        <!-- CTA Section -->
        <section id="cta" class="py-16 text-center">
            <h2 class="text-3xl md:text-4xl font-bold mb-4">Готові підвищити видимість?</h2>
            <p class="text-lg text-gray-400 mb-8">
                Завантажте файл, щоб дізнатися, чи ваші продукти готові до ери ШІ-пошуку.
            </p>
            <div class="bg-gray-800 p-8 rounded-2xl max-w-2xl mx-auto shadow-lg">
                <form id="uploadForm" class="space-y-6">
                    <div>
                        <label for="email" class="block text-gray-400 mb-2 text-left">Ваш Email</label>
                        <input type="email" id="email" name="email" required placeholder="your.email@company.com" class="w-full p-3 rounded-lg bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label for="file" class="block text-gray-400 mb-2 text-left">Завантажте файл (CSV/XLSX)</label>
                        <input type="file" id="file" name="file" accept=".csv,.xlsx,.tsv" required class="w-full p-3 rounded-lg bg-gray-700 border border-gray-600 text-gray-300">
                        <small class="text-gray-500 mt-2 block text-left">
                            Підтримувані формати: CSV, XLSX, TSV (Макс. 10МБ)
                        </small>
                    </div>
                    <button type="submit" class="w-full py-3 rounded-full text-white font-bold shadow-lg hover-lift gradient-button-blue">
                        Аналізувати видимість
                    </button>
                </form>
                <div id="status" class="status mt-4 text-left"></div>
            </div>
        </section>

        <!-- Final CTA section -->
        <section id="final-cta" class="py-16 text-center">
            <a href="#cta" class="py-3 px-8 rounded-full text-white font-bold shadow-xl hover-lift inline-block gradient-button">
                Почати аналіз
            </a>
        </section>
    </main>

    <!-- Footer -->
    <footer class="footer text-center text-gray-500">
        <p>&copy; 2024 BoostMyGEO. Всі права захищені.</p>
    </footer>

    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const statusDiv = document.getElementById('status');
            const submitBtn = e.target.querySelector('button[type="submit"]');
            
            // Reset status
            statusDiv.style.display = 'none';
            statusDiv.className = '';
            
            // Disable submit button
            submitBtn.disabled = true;
            submitBtn.innerHTML = '⏳ Обробка...';
            
            // Get form data
            const formData = new FormData();
            formData.append('email', document.getElementById('email').value);
            formData.append('file', document.getElementById('file').files[0]);
            
            try {
                const response = await fetch('/api/submit', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    statusDiv.className = 'status success bg-green-900 text-green-300 p-4 rounded-xl';
                    statusDiv.innerHTML = `
                        <strong>✅ Успіх!</strong><br>
                        Файл отримано та обробляється.<br>
                        Звіт буде надіслано на <strong>${result.email}</strong> протягом 5-10 хвилин.
                    `;
                    
                    document.getElementById('uploadForm').reset();
                } else {
                    statusDiv.className = 'status error bg-red-900 text-red-300 p-4 rounded-xl';
                    statusDiv.innerHTML = `
                        <strong>❌ Помилка:</strong><br>
                        ${result.detail || 'Помилка завантаження'}
                    `;
                    throw new Error(result.detail || 'Upload failed');
                }
            } catch (error) {
                statusDiv.className = 'status error bg-red-900 text-red-300 p-4 rounded-xl';
                statusDiv.innerHTML = `
                    <strong>❌ Помилка:</strong><br>
                    ${error.message}
                `;
            } finally {
                // Re-enable submit button
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Аналізувати видимість';
                statusDiv.style.display = 'block';
            }
        });
        
        // File validation - Updated to use custom modal
        document.getElementById('file').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const maxSize = 10 * 1024 * 1024; // 10MB
                if (file.size > maxSize) {
                    showCustomModal('Файл занадто великий. Максимальний розмір 10МБ.');
                    e.target.value = '';
                    return;
                }
                
                const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/tsv'];
                if (!validTypes.includes(file.type) && !file.name.match(/\\.(csv|xlsx|tsv)$/i)) {
                    showCustomModal('Неправильний тип файлу. Будь ласка, завантажуйте лише файли CSV, XLSX або TSV.');
                    e.target.value = '';
                    return;
                }
            }
        });

        function showCustomModal(message) {
            const modal = document.createElement('div');
            modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 1000;';
            modal.innerHTML = `
                <div style="background: #1f2937; padding: 2rem; border-radius: 1rem; text-align: center; max-width: 400px; box-shadow: 0 10px 20px rgba(0,0,0,0.2);">
                    <p style="color: #f3f4f6; font-size: 1.125rem; margin-bottom: 1.5rem;">${message}</p>
                    <button onclick="this.parentElement.parentElement.remove()" style="background: #3b82f6; color: white; padding: 0.75rem 1.5rem; border-radius: 9999px; font-weight: bold;">Закрити</button>
                </div>
            `;
            document.body.appendChild(modal);
        }

        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.feature-card').forEach(el => {
            observer.observe(el);
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
    Создание CSV шаблона в памяти с правильными данными
    
    Returns:
        Bytes содержимого CSV файла
    """
    template_data = {
        'Country': [
            'UK', 'USA', 'Germany', 'UK', 'USA',
            'Germany', 'UK', 'USA', 'Germany', 'UK'
        ],
        'Prompt': [
            'Dyson V15 cordless vacuum cleaner best price UK',
            'KitchenAid stand mixer reviews USA', 
            'Samsung Waschmaschine 9kg Frontlader Deutschland',
            'Ninja air fryer large capacity reviews UK',
            'Bosch dishwasher built-in stainless steel USA',
            'Miele Waschmaschine Test Deutschland',
            'Shark vacuum cleaner cordless UK best',
            'Instant Pot pressure cooker reviews USA',
            'AEG Geschirrspüler Einbau Deutschland',
            'Russell Hobbs kettle best price UK'
        ],
        'Website': [
            'amazon.com', 'amazon.com', 'amazon.de', 'amazon.co.uk', 'amazon.com',
            'amazon.de', 'amazon.co.uk', 'amazon.com', 'amazon.de', 'amazon.co.uk'
        ]
    }
    
    df = pd.DataFrame(template_data)
    
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
        queries_df, processed_count = FileProcessor.process_file(file_path)
        
        results = []
        
        for _, row in queries_df.iterrows():
            country = row['Country']
            prompt = row['Prompt']
            target_domain = row['target_domain']
            
            geo_prompt = create_geo_targeted_prompt(prompt, country)
            
            search_result = openai_client.search_with_web(geo_prompt)
            sources = search_result["sources"]
            usage = search_result["usage"]
            
            metrics = MetricsCalculator.calculate_metrics_for_query(
                sources, target_domain, country
            )
            
            result_row = {
                "Оригинальный промпт": prompt,
                "Геотаргетированный промпт": geo_prompt,
                **metrics,
                "Tokens Used": getattr(usage, "total_tokens", None) if usage else None
            }
            
            results.append(result_row)
        
        results_df = pd.DataFrame(results)
        csv_content = results_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        
        db.save_email(email, ip)
        
        email_service.send_report_email(email, csv_content, len(results))
        
    except Exception as e:
        print(f"Ошибка обработки файла: {e}")
    finally:
        try:
            os.remove(file_path)
        except:
            pass

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    try:
        validate_config()
        print("✅ Конфигурация проверена")
        print("✅ База данных инициализирована")
        print("✅ AI Visibility MVP запущен")
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        pass

@app.get("/")
async def serve_landing():
    """Отдача лендинг страницы"""
    return HTMLResponse(content=LANDING_HTML, status_code=200)

@app.get("/api/download-template")
async def download_template():
    """
    Эндпоинт для скачивания шаблона CSV файла
    
    Returns:
        CSV файл с примерами
    """
    csv_bytes = create_template_csv()
    
    headers = {
        "Content-Disposition": "attachment; filename=ai_visibility_template.csv",
        "Content-Type": "text/csv; charset=utf-8",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    
    return StreamingResponse(
        BytesIO(csv_bytes),
        media_type="text/csv",
        headers=headers
    )

@app.post("/api/submit")
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
    if not EMAIL_REGEX.match(email):
        raise HTTPException(status_code=400, detail="Неверный формат email")
    
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Ошибка чтения файла")
    
    try:
        FileProcessor.validate_file_size(content, MAX_UPLOAD_MB)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    client_ip = get_client_ip(request)
    file_hash = hashlib.sha256(content).hexdigest()
    
    try:
        db.check_ip_file_access(client_ip, file_hash, ALLOW_RETRY_SAME_FILE)
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        print(f"Database warning: {e}")
        pass
    
    file_extension = FileProcessor.get_file_extension(file.filename)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка сохранения файла")
    
    worker_thread = threading.Thread(
        target=process_file_worker,
        args=(temp_file_path, email, client_ip),
        daemon=True
    )
    worker_thread.start()
    
    return JSONResponse({
        "ok": True,
        "email": email,
        "status": "processing",
        "message": "Файл прийнято в обробку. Очікуйте звіт на email."
    })

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {"status": "ok", "service": "AI Visibility MVP"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
