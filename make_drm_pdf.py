import sys
import io
import os
import pikepdf
from reportlab.pdfgen import canvas

# Windows 환경에서 한글 콘솔 출력 깨짐 방지
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def create_and_encrypt_pdf():
    pdf_filename = "protected_doc.encrypted.pdf"
    temp_pdf = "temp_plain.pdf"
    password = "company_secret_key"
    
    try:
        # 1. 임시 일반 PDF 생성 (텍스트 내용 추가)
        c = canvas.Canvas(temp_pdf)
        c.drawString(100, 750, "CONFIDENTIAL DOCUMENT - FOR INTERNAL USE ONLY")
        c.drawString(100, 720, "This is an encrypted document representing secure enterprise data.")
        c.drawString(100, 690, "Security Key: company_secret_key")
        c.drawString(100, 660, "Topic: Secret Project Beta Launch Protocol")
        c.drawString(100, 630, "- Server host address: 10.150.22.41")
        c.drawString(100, 600, "- Launch Date: October 15, 2026")
        c.drawString(100, 570, "Keep this information secure.")
        c.save()
        
        # 2. pikepdf를 통한 AES-256 표준 암호화 적용
        with pikepdf.open(temp_pdf) as pdf:
            pdf.save(
                pdf_filename,
                encryption=pikepdf.Encryption(
                    owner=password,
                    user=password,
                    R=6  # AES-256 비트 암호화
                )
            )
        print(f"[성공] 암호화된 PDF 파일 생성 완료: {pdf_filename}")
        
    except Exception as e:
        print(f"[에러] PDF 생성 중 에러 발생: {e}")
        
    finally:
        # 임시 평문 PDF 삭제
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
            print("[정리] 임시 평문 파일 삭제 완료.")

if __name__ == "__main__":
    create_and_encrypt_pdf()
