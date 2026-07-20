import os
import json
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from service.jobs_service import get_all_job_names

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


class BankExperienceDetail(BaseModel):
    kinh_nghiem: Literal[
        "Chưa có kinh nghiệm",
        "Dưới 1 năm kinh nghiệm",
        "Từ 1-3 năm kinh nghiệm",
        "Từ 3-5 năm kinh nghiệm",
        "Trên 5 năm kinh nghiệm",
    ] = Field(description="Phân loại kinh nghiệm ngân hàng")
    
    da_lam_viec_o: list = Field(
        default=[],
        description="Danh sách tên ngân hàng/công ty tài chính đã làm việc"
    )


class CVStructure(BaseModel):
    ho_va_ten: str = Field(
        description=(
            "Họ tên ứng viên đầy đủ với dấu tiếng Việt. "
            "Nằm ở dòng đầu tiên hoặc font chữ lớn nhất ở đầu trang 1. "
            "Loại trừ các từ tiêu đề như 'Curriculum Vitae', 'Resume', 'CV'. "
            "Nếu input là 'Nguyen Nhat Bang' → 'Nguyễn Nhật Bằng'"
        )
    )

    dob: str = Field(
        description=(
            "Năm sinh (chỉ lấy năm, không lấy ngày/tháng). "
            "Tìm 'Năm sinh', 'Ngày sinh', 'DOB', 'D.O.B', 'dob'. "
            "Nếu không có → để trống '', không được None"
        )
    )

    so_dien_thoai: str = Field(
        description=(
            "Số điện thoại 10-15 ký tự, chỉ giữ số và dấu + ở đầu. "
            "QUY TẮC CHUYỂN ĐỔI: "
            "- Nếu bắt đầu '84' → chuyển thành '0' (ví dụ: 845678988 → 05678988) "
            "- Nếu bắt đầu '+84' → chuyển thành '0' (ví dụ: +845678988 → 05678988) "
            "- Ngoài ra giữ nguyên. "
            "Loại bỏ khoảng trắng, -, (), chỉ giữ số. "
            "Nếu không có → để trống '', không được None"
        )
    )

    email: str = Field(
        description="Địa chỉ email chuẩn. Nếu không có → để trống ''"
    )

    gioi_tinh: Literal["Nam", "Nữ", ""] = Field(
        description=(
            "QUAN TRỌNG: Phân tích 'Họ và tên' hoặc tìm từ khóa. "
            "Ví dụ: tên đệm 'Thị' thường là Nữ, 'Văn' thường là Nam. "
            "Hoặc tìm 'Nam'/'Nữ', 'Male'/'Female' trong CV. "
            "TUYỆT ĐỐI KHÔNG ĐƯỢC ĐOÁN giới tính chỉ dựa vào tên nếu không chắc chắn. "
            "Nếu không chắc → để trống '', không được None"
        )
    )

    noi_o: str = Field(
        description=(
            "Chỉ trích xuất TÊN THÀNH PHỐ/TỈNH THÀNH Việt Nam. "
            "Ưu tiên mục Contact Info/Address ở đầu, sau đó Experience gần nhất. "
            "Ví dụ: '123 đường ABC, phường X, quận Y, Hà Nội' → chỉ lấy 'Hà Nội'. "
            "Nếu không có → để trống '', không được None"
        )
    )

    vi_tri_ung_tuyen: str = Field(
        description=(
            "BẮTBUỘC PHẢI CÓ, KHÔNG ĐƯỢC ĐỂ TRỐNG. "
            "Phải ánh xạ đúng từ danh sách Job được cung cấp. "
            "Không được sinh ra vị trí mới ngoài danh sách. "
            "Không lấy số thứ tự nếu có. "
            "Tìm từ: "
            "1. Chức danh gần tên ứng viên ở phần intro "
            "2. Phần nguyện vọng (Objective) "
            "3. Vị trí gần đây nhất trong Experience"
        )
    )

    so_nam_kinh_nghiem: Literal[
        "Chưa có kinh nghiệm",
        "Dưới 1 năm kinh nghiệm",
        "Từ 1-3 năm kinh nghiệm",
        "Từ 3-5 năm kinh nghiệm",
        "Trên 5 năm kinh nghiệm",
    ] = Field(
        description=(
            "Tổng kinh nghiệm làm việc từ tất cả vị trí được đánh giá phù hợp "
            "với vi_tri_ung_tuyen. Chỉ tính vị trí Match. "
            "Hợp nhất khoảng thời gian chồng lắp, không tính trùng. "
            "Phân loại dựa trên tháng (không dựa trên năm làm tròn): "
            "- 0 tháng → 'Chưa có kinh nghiệm' "
            "- 1-11 tháng → 'Dưới 1 năm kinh nghiệm' "
            "- 12-35 tháng → 'Từ 1-3 năm kinh nghiệm' "
            "- 36-59 tháng → 'Từ 3-5 năm kinh nghiệm' "
            "- 60+ tháng → 'Trên 5 năm kinh nghiệm'"
        )
    )

    so_nam_kinh_nghiem_bank: BankExperienceDetail = Field(
        description=(
            "CHỈ TÍNH KINH NGHIỆM TẠI: "
            "Ngân hàng (VCB, Techcombank, BIDV, v.v), "
            "Chứng khoán (SSI, VPS, HSC, v.v), "
            "Bảo hiểm (Prudential, Manulife, AIA, v.v), "
            "Fintech tài chính (MoMo, ZaloPay, VNPay), "
            "Công ty tài chính/tín dụng (FE Credit, Home Credit, v.v). "
            "NHẬN DIỆN MỞ RỘNG: "
            "'dự án tại <tên bank>', 'project tại <tên bank>', "
            "'khách hàng <tên bank>', 'Tester của dự án X tại MSB - 10/2024 - nay'. "
            "Quy tắc tính toán giống kinh nghiệm chung. "
            "Nếu không có → {kinh_nghiem: 'Chưa có kinh nghiệm', da_lam_viec_o: []}"
        )
    )

    tech_skill: list = Field(
        description=(
            "Danh sách kỹ năng kỹ thuật (mảng/array). "
            "Tìm mục 'Technical Skills', 'Skills', 'Tech Stack', 'Technologies'. "
            "Chỉ giữ NGÔN NGỮ, FRAMEWORK, DATABASE, CÔNG CỤ, NỀN TẢNG. "
            "VÍ DỤ GIỮ: Python, Java, React, Docker, AWS, MySQL, REST API. "
            "VÍ DỤ LOẠI BỎ: Teamwork, Communication, Problem-solving, "
            "'Software Engineer', 'Bachelor of Computer Science'. "
            "Nếu có 'Tech stack: Python, FastAPI' → chỉ lấy các tech skill. "
            "Trả về mảng, ví dụ: ['Python', 'Docker', 'Kubernetes']"
        )
    )

    thoi_gian_onboard: str = Field(
        description=(
            "Trích xuất từ caption/extra_info (không lấy từ CV). "
            "Tìm từ khóa 'onboard', 'Thời gian onboard'. "
            "Ví dụ: 'onboard 10/10' → '10/10'. "
            "Nếu không có → để trống '', không được None"
        )
    )

    luong: str = Field(
        description=(
            "Trích xuất từ caption/extra_info (không lấy từ CV). "
            "Tìm từ khóa 'lương', 'salary', 'mức lương'. "
            "Ví dụ: 'lương 10tr' → '10tr', 'lương 30 triệu' → '30 triệu'. "
            "Nếu không có → để trống '', không được None"
        )
    )

    doi_tac: str = Field(
        description=(
            "CHỈ trích xuất từ caption/extra_info, KHÔNG từ CV. "
            "Không được lấy công ty, tổ chức, partner, khách hàng từ CV. "
            "Tìm từ khóa: 'đối tác', 'partner', 'khách', 'client', 'cooperation'. "
            "Hoặc tên riêng đứng cuối caption với vai trò đối tác. "
            "Ví dụ: 'onboard 10/10, lương 10tr, anh Phượng' → ánh xạ 'Phượng' về tên chuẩn. "
            "Nếu không có từ khóa đối tác trong caption → để trống '', không được None"
        )
    )

    ghi_chu: str = Field(
        description=(
            "Gộp 'Thời gian onboard' và 'Lương' từ caption. "
            "Format: 'Thời gian onboard: <giá trị>, Lương: <giá trị>' "
            "Nếu chỉ có một → chỉ ghi cái đó. "
            "Ví dụ: 'onboard 10/10, lương 10tr' → 'Thời gian onboard: 10/10, Lương: 10tr'. "
            "Ví dụ: 'lương 12tr' → 'Lương: 12tr'. "
            "Nếu không có caption → để trống '', không được None"
        )
    )


def extract_cv(text: str, caption: str = "", job=None, current_date: str = None) -> dict:
    """
    Bóc tách thông tin CV từ văn bản thô.
    
    Args:
        text: Nội dung CV thô
        caption: Thông tin bổ sung (onboard, lương, đối tác)
        job: Vị trí ứng tuyển được chọn sẵn (nếu có)
        current_date: Ngày hiện tại để tính kinh nghiệm (format: DD/MM/YYYY)
    
    Returns:
        dict: Thông tin CV được bóc tách theo cấu trúc
    """
    
    jobs = get_all_job_names()

    job_list = "\n".join(
        f"- {item}"
        for item in jobs
    )

    # System prompt chi tiết bao phủ tất cả quy tắc từ N8N
    system_prompt = f"""Bạn là chuyên gia HR cao cấp chuyên bóc tách CV. Tuân thủ TUYỆT ĐỐI các quy tắc sau:

=== DANH SÁCH VỊ TRÍ HỢP LỆ ===
{job_list}

Vị trí ứng tuyển PHẢI nằm trong danh sách trên. KHÔNG ĐƯỢC sinh ra vị trí mới dù giống nghĩa hay viết tắt.

=== QUY TẮC THEO FIELD ===

1. HỌ VÀ TÊN:
   - Đầy đủ với dấu tiếng Việt
   - Ở dòng đầu tiên hoặc font lớn nhất đầu trang
   - Loại trừ 'Curriculum Vitae', 'Resume', 'CV'
   - Nếu nhập 'Nguyen Nhat Bang' → chuyển thành 'Nguyễn Nhật Bằng'

2. NĂM SINH (DoB):
   - Chỉ lấy NĂMS, không lấy ngày/tháng
   - Tìm 'Năm sinh', 'Ngày sinh', 'DOB', 'D.O.B', 'dob'
   - Nếu không → để trống ""

3. SỐ ĐIỆN THOẠI:
   - QUY TẮC CHUYỂN ĐỔI BẮT BUỘC:
     * 84XXXXXXXX → 0XXXXXXXX (ví dụ: 845678988 → 05678988)
     * +84XXXXXXXX → 0XXXXXXXX (ví dụ: +845678988 → 05678988)
     * Ngoài ra giữ nguyên
   - Loại bỏ khoảng trắng, dấu gạch, ngoặc
   - Nếu không → để trống ""

4. EMAIL:
   - Trích xuất email chuẩn
   - Nếu không → để trống ""

5. GIỚI TÍNH:
   - Phân tích tên đệm: 'Thị'→ Nữ, 'Văn'→ Nam (nếu có)
   - Hoặc tìm từ khóa: 'Nam', 'Nữ', 'Male', 'Female'
   - TUYỆT ĐỐI không đoán nếu không chắc chắn
   - Nếu không → để trống ""

6. NƠI Ở:
   - Chỉ tên THÀNH PHỐ/TỈNH THÀNH Việt Nam
   - '123 đường ABC, quận Y, Hà Nội' → 'Hà Nội'
   - Ưu tiên Contact Info, sau đó Experience gần nhất
   - Nếu không → để trống ""

7. VỊ TRÍ ỨNG TUYỂN:
   - BẮT BUỘC PHẢI CÓ, KHÔNG ĐỂ TRỐNG
   - Phải ĐÚNG từ danh sách trên
   - Tìm: chức danh gần tên → Objective/Nguyện vọng → Experience gần nhất
   - Nếu user chọn sẵn → bắt buộc dùng giá trị đó
   - Nếu tự động → phân tích CV chọn vị trí hợp lý từ danh sách

8. KINH NGHIỆM CHUNG (Số năm kinh nghiệm):
   - Tìm toàn bộ lịch sử công việc có đầy đủ: công ty, vị trí, thời gian
   - Chỉ cộng vị trí MATCH với vi_tri_ung_tuyen
   - Hợp nhất khoảng trùng lắp, không tính kép
   - Tính toán chi tiết từng tháng
   - Ngày hiện tại để tính: {current_date or 'lấy từ hệ thống'}
   - Phân loại:
     * 0 tháng → 'Chưa có kinh nghiệm'
     * 1-11 tháng → 'Dưới 1 năm kinh nghiệm'
     * 12-35 tháng → 'Từ 1-3 năm kinh nghiệm'
     * 36-59 tháng → 'Từ 3-5 năm kinh nghiệm'
     * 60+ tháng → 'Trên 5 năm kinh nghiệm'

9. KINH NGHIỆM NGÂN HÀNG (Số năm kinh nghiệm Bank):
   - CHỈ TÍNH:
     * Ngân hàng (Techcombank, BIDV, VCB, VPBank, TPBank, v.v)
     * Chứng khoán (SSI, VPS, HSC, MBS, VCBS, v.v)
     * Bảo hiểm (Prudential, Manulife, AIA, Sun Life, Bảo Việt, PVI, v.v)
     * Fintech tài chính (MoMo, ZaloPay, VNPay, Onepay, v.v)
     * Công ty tài chính (FE Credit, Home Credit, Mcredit, JACCS, AEON Credit, v.v)
   - NHẬN DIỆN MỞ RỘNG:
     * 'dự án tại <tên bank>'
     * 'project tại <tên bank>'
     * 'khách hàng <tên bank>'
     * 'Tester của dự án Magnet tại MSB - 10/2024 - nay' → tính là kinh nghiệm MSB
     * 'Tester/BA - Dự án chuyển đổi Core banking tại VCB Neo - 8/2022 - 10/2024'
   - Quy tắc tính toán giống kinh nghiệm chung
   - Output: {{"kinh_nghiem": "<phân loại>", "da_lam_viec_o": [<danh sách công ty>]}}
   - Nếu không có → {{"kinh_nghiem": "Chưa có kinh nghiệm", "da_lam_viec_o": []}}

10. KỸ NĂNG KỸ THUẬT (Tech_Skill):
    - Tìm mục: 'Technical Skills', 'Skills', 'Tech Stack', 'Technologies', 'Tools'
    - Chỉ GIỮ: Ngôn ngữ, Framework, Database, Công cụ, Nền tảng
    - VÍ DỤ GIỮ: Python, Java, React, Docker, Kubernetes, AWS, MySQL, REST API, FastAPI
    - VÍ DỤ LOẠI BỎ: Teamwork, Communication, Problem-solving, Software Engineer, Bachelor degree
    - Nếu 'Tech stack: Python, FastAPI' → chỉ lấy tech skill, không lấy cả câu
    - Trả về mảng

11. THỜI GIAN ONBOARD:
    - CHỈ từ caption/extra_info (KHÔNG từ CV)
    - Tìm từ khóa: 'onboard', 'ngày onboard'
    - Ví dụ: 'onboard 10/10' → '10/10'
    - Nếu không → để trống ""

12. LƯƠNG:
    - CHỈ từ caption/extra_info (KHÔNG từ CV)
    - Tìm từ khóa: 'lương', 'salary'
    - Ví dụ: 'lương 10tr' → '10tr', 'lương 30 triệu' → '30 triệu'
    - Nếu không → để trống ""

13. ĐỐI TÁC:
    - CHỈ từ caption/extra_info, KHÔNG từ CV
    - Không lấy công ty/tổ chức/khách hàng từ CV
    - Tìm từ khóa: 'đối tác', 'partner', 'khách', 'client', 'cooperation'
    - Hoặc tên riêng ở cuối caption
    - Ví dụ: 'lương 10tr, anh Phượng' → ánh xạ 'Phượng' về tên chuẩn
    - Nếu không có từ khóa → để trống ""

14. GHI CHÚ (Note):
    - Gộp 'Thời gian onboard' + 'Lương' từ caption
    - Format: 'Thời gian onboard: <giá trị>, Lương: <giá trị>'
    - Nếu chỉ có một → ghi cái đó
    - Ví dụ: 'onboard 10/10, lương 10tr' → 'Thời gian onboard: 10/10, Lương: 10tr'
    - Nếu không → để trống ""

=== QUY TẮC CHUNG ===
- Không suy diễn, không tự bổ sung thông tin
- Nếu không tìm thấy → để trống "" (KHÔNG phải None)
- Tuân thủ tuyệt đối định dạng output JSON
- Bất kỳ trường không tìm thấy → để trống "", không bỏ qua"""

    # Thêm quy tắc bắt buộc job nếu user chọn sẵn
    if job and job != "Auto Detect":
        system_prompt += f"""

=== QUY TẮC VỊ TRÍ CỤ THỀ ===
CV này đã được chọn vị trí: '{job}'
BẮT BUỘC: giá trị 'vi_tri_ung_tuyen' PHẢI là '{job}'"""

    # Chuẩn bị content cho API
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"""Nội dung CV cần xử lý:

{text}

{"Caption/Thông tin bổ sung: " + caption if caption else ""}""",
        },
    ]

    # Call OpenAI API với structured output
    response = client.beta.messages.parse(
        model="gpt-4-turbo",  # Đổi từ gpt-5-mini nếu không tồn tại
        messages=messages,
        response_format=CVStructure,
    )

    result = response.content[0].model_dump()
    
    # Đảm bảo so_nam_kinh_nghiem_bank là dict đúng định dạng
    if isinstance(result.get("so_nam_kinh_nghiem_bank"), dict):
        if "kinh_nghiem" not in result["so_nam_kinh_nghiem_bank"]:
            result["so_nam_kinh_nghiem_bank"] = {
                "kinh_nghiem": "Chưa có kinh nghiệm",
                "da_lam_viec_o": []
            }
    
    return result


# Ví dụ sử dụng
if __name__ == "__main__":
    sample_cv = """
    NGUYỄN NHẬT BẰNG
    Email: bang.nguyen@example.com | Phone: 0987654321
    Hà Nội
    
    OBJECTIVE: Tìm vị trí Software Engineer
    
    WORK EXPERIENCE:
    
    GlobalTech Solutions | Senior Software Engineer | 01/2020 - Present
    - Phát triển backend với Python, FastAPI
    - Thiết kế database PostgreSQL
    - Deploy với Docker, Kubernetes trên AWS
    
    TechStart Vietnam | Software Engineer | 06/2018 - 12/2019
    - Xây dựng REST API với Java, Spring Boot
    - Làm việc với MySQL database
    
    TECHNICAL SKILLS:
    Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, 
    Java, Spring Boot, MySQL, REST API, Git
    
    EDUCATION:
    Bachelor of Computer Science - Hanoi University of Technology (2018)
    """
    
    sample_caption = "onboard 15/03/2025, lương 25 triệu, anh Phương"
    current_date = "15/03/2025"
    
    result = extract_cv(
        text=sample_cv,
        caption=sample_caption,
        job="Software Engineer",
        current_date=current_date
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
