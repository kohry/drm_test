import os
import sys
import io
import boto3
import pikepdf
from pypdf import PdfReader
from fastmcp import FastMCP
from dotenv import load_dotenv

# Windows 환경에서 한글 로그 출력 깨짐 방지
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 로컬 테스트 시 .env 로드
load_dotenv()

# S3 호환 설정 로드
access_key = os.getenv("NCP_ACCESS_KEY")
secret_key = os.getenv("NCP_SECRET_KEY")
bucket_name = os.getenv("NCP_BUCKET", "ce-mcp-practice")
endpoint_url = os.getenv("NCP_ENDPOINT_URL", "https://kr.object.ncloudstorage.com")

# DRM 암호화 해제 비밀번호 설정 (기본값: company_secret_key)
DRM_PASSWORD = os.getenv("DRM_PASSWORD", "company_secret_key")

# boto3 S3 클라이언트 초기화
s3 = boto3.client(
    "s3",
    endpoint_url=endpoint_url,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
)

# FastMCP 서버 인스턴스 생성
mcp = FastMCP("naver-cloud-document-mcp")

@mcp.tool()
def list_documents() -> list[str]:
    """NAVER Cloud Object Storage 버킷에 존재하는 모든 문서 파일(Key) 목록을 반환합니다."""
    try:
        print("[Tool Call] list_documents 호출됨")
        response = s3.list_objects_v2(Bucket=bucket_name)
        contents = response.get("Contents", [])
        return [obj["Key"] for obj in contents]
    except Exception as e:
        print(f"[Error] list_documents 실패: {e}")
        return [f"Error listing documents: {str(e)}"]

@mcp.tool()
def read_document(filename: str) -> str:
    """
    지정한 문서 파일(filename)의 내용을 읽어서 반환합니다.
    - 일반 텍스트 파일(.txt)은 utf-8 텍스트로 디코딩합니다.
    - 암호화된 PDF 파일(.pdf)은 메모리(io.BytesIO) 상에서 복호화한 후 텍스트를 추출하여 반환합니다.
    """
    try:
        print(f"[Tool Call] read_document 호출됨 (파일명: {filename})")
        
        # 1. 스토리지에서 파일 바이너리 가져오기
        response = s3.get_object(Bucket=bucket_name, Key=filename)
        file_bytes = response["Body"].read()

        # 2. PDF 파일인 경우 (DRM 복호화 프로세스 수행)
        if filename.lower().endswith(".pdf"):
            print(f"[처리] '{filename}' PDF 파일 감지. In-Memory 복호화 시작...")
            
            # 입력 바이트를 메모리 버퍼로 래핑
            input_stream = io.BytesIO(file_bytes)
            output_stream = io.BytesIO()
            
            # pikepdf를 통해 메모리 단에서 DRM 복호화 진행
            try:
                with pikepdf.open(input_stream, password=DRM_PASSWORD) as pdf:
                    pdf.save(output_stream)
                output_stream.seek(0)
                print("[성공] In-Memory 복호화 완료.")
            except pikepdf.PasswordError:
                return f"Error: '{filename}'의 복호화 비밀번호가 올바르지 않습니다."
            except Exception as pdf_err:
                return f"Error decrypting PDF: {str(pdf_err)}"
            finally:
                input_stream.close()

            # pypdf를 사용하여 메모리 스트림에서 텍스트 추출
            try:
                reader = PdfReader(output_stream)
                text_list = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    text_list.append(f"--- [Page {i + 1}] ---\n{text}")
                
                output_stream.close()
                return "\n".join(text_list)
            except Exception as txt_err:
                return f"Error extracting text from PDF: {str(txt_err)}"

        # 3. 일반 텍스트 파일인 경우
        else:
            return file_bytes.decode("utf-8")

    except Exception as e:
        print(f"[Error] read_document '{filename}' 실패: {e}")
        return f"Error reading document '{filename}': {str(e)}"

if __name__ == "__main__":
    # Cloud Run 및 로컬 포트 대응 (기본값 8080)
    port = int(os.getenv("PORT", 8080))
    print(f"Starting MCP server on port {port} with streamable-http...")
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        path="/mcp"
    )
