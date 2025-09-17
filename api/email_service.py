"""
Сервис для отправки email уведомлений с результатами анализа
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_TLS

class EmailService:
    """Сервис для отправки email уведомлений"""
    
    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_pass = SMTP_PASS
        self.smtp_from = SMTP_FROM
        self.smtp_tls = SMTP_TLS
    
    def send_report_email(self, recipient_email: str, csv_content: bytes, queries_count: int) -> bool:
        """
        Отправка email с отчетом
        
        Args:
            recipient_email: Email получателя
            csv_content: Содержимое CSV файла в байтах
            queries_count: Количество обработанных запросов
            
        Returns:
            True если отправлено успешно, False иначе
        """
        try:
            # Создание email сообщения
            msg = MIMEMultipart()
            msg['From'] = self.smtp_from
            msg['To'] = recipient_email
            msg['Subject'] = f"AI Visibility Analysis Report - {queries_count} queries processed"
            
            # Текст сообщения
            body = f"""
            Hello!
            
            Your AI Visibility analysis has been completed successfully.
            
            Analysis Summary:
            - Total queries processed: {queries_count}
            - Analysis includes AIV-Score, competitor analysis, and geo-targeting results
            - Results are attached as CSV file for further analysis
            
            Key metrics included:
            • AIV-Score (0-100) for each query and domain
            • Best ranking position in AI search results  
            • Competitor strength analysis
            • Geographic targeting results
            • Source coverage analysis
            
            Thank you for using AI Visibility Analytics!
            
            Best regards,
            AI Visibility Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Прикрепление CSV файла
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(csv_content)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="ai_visibility_report_{queries_count}_queries.csv"'
            )
            msg.attach(attachment)
            
            # Отправка email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)
                
                server.send_message(msg)
            
            print(f"✅ Email отправлен на {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Тестирование подключения к SMTP серверу
        
        Returns:
            True если подключение успешно, False иначе
        """
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_pass:
                    server.login(self.smtp_user, self.smtp_pass)
            
            print("✅ SMTP подключение успешно")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка SMTP подключения: {e}")
            return False

# Глобальный экземпляр email сервиса
email_service = EmailService()