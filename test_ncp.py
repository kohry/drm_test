import os
import sys
import io
import boto3
import pikepdf
from pypdf import PdfReader
from dotenv import load_dotenv

# Windows 환경에서 한글 및 이모지 콘솔 출력 시 인코딩(UTF-8) 문제를 방지하기 위한 설정
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# .env 파일에서 환경변수 로드
load_dotenv()

access_key = os.getenv("NCP_ACCESS_KEY")
secret_key = os.getenv("NCP_SECRET_KEY")
bucket_name = os.getenv("NCP_BUCKET")
endpoint_url = os.getenv("NCP_ENDPOINT_URL", "https://kr.object.ncloudstorage.com")
DRM_PASSWORD = "company_secret_key"

def test_drm_decryption():
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        
        filename = "protected_doc.encrypted.pdf"
        print(f"\n[조회] 버킷에서 '{filename}' 다운로드를 시작합니다 (In-Memory)...")
        
        # 1. 파일 바이너리 받아오기
        response = s3.get_object(Bucket=bucket_name, Key=filename)
        file_bytes = response["Body"].read()
        print(f"[성공] 파일 바이너리 획득 완료: {len(file_bytes)} bytes")

        # 2. BytesIO 메모리 스트림 설정
        input_stream = io.BytesIO(file_bytes)
        output_stream = io.BytesIO()

        # 3. pikepdf 메모리 복호화
        print("[복호화] pikepdf를 통한 In-Memory 복호화를 시도합니다...")
        with pikepdf.open(input_stream, password=DRM_PASSWORD) as pdf:
            pdf.save(output_stream)
        output_stream.seek(0)
        print("[성공] 복호화 스트림 생성 완료.")

        # 4. pypdf 텍스트 추출
        print("[텍스트 추출] pypdf로 PDF 내용 파싱 시작...")
        reader = PdfReader(output_stream)
        
        print("\n=== [추출된 텍스트 내용] ===")
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            print(f"--- Page {i + 1} ---")
            print(text.strip())
        print("============================\n")

        # 스트림 리소스 클리어
        input_stream.close()
        output_stream.close()
        print("[성공] 모든 자원이 메모리에서 정상적으로 해제되었습니다.")

    except Exception as e:
        print(f"\n❌ 에러가 발생했습니다: {e}")

if __name__ == "__main__":
    test_drm_decryption()
