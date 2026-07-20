import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from service.jobs_service import get_all_job_names

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


class CVStructure(BaseModel):
    full_name: str = Field(
        description=(
            "Họ tên ứng viên. Nguyên tắc: Nằm ở dòng đầu tiên hoặc font chữ lớn nhất ở đầu trang 1. "
            "Loại trừ các từ tiêu đề như 'Curriculum Vitae', 'Resume', 'CV'. "
            "Lấy chuỗi Title Case hoặc UPPER CASE ở top header."
        )
    )

    gender: Literal["Nam", "Nữ", "Không rõ"] = Field(
        description=(
            "Tìm từ khóa định danh: 'Male'/'Female'/'Nam'/'Nữ'. "
            "Không thấy thì trả về 'Không rõ'. "
            "TUYỆT ĐỐI không đoán giới tính dựa trên tên."
        )
    )

    email: str = Field(
        description="Địa chỉ email chuẩn."
    )

    phone: str = Field(
        description=(
            "Số điện thoại 10-15 ký tự. "
            "Loại bỏ khoảng trắng, -, (), chỉ giữ số và dấu + ở đầu."
        )
    )

    city: str = Field(
        description=(
            "Thành phố/Tỉnh thành tại Việt Nam. "
            "Ưu tiên Header/Contact Info, sau đó Experience gần nhất."
        )
    )

    job_name: str = Field(
        description=(
            "Vị trí ứng tuyển thích hợp. "
            "Phải ánh xạ về đúng danh sách vị trí được cung cấp."
        )
    )

    exp: Literal[
        "Chưa có kinh nghiệm",
        "Dưới 1 năm kinh nghiệm",
        "Từ 1-3 năm kinh nghiệm",
        "Từ 3-5 năm kinh nghiệm",
        "Trên 5 năm kinh nghiệm",
    ] = Field(
        description=(
            "Tổng thời gian của tất cả vị trí được đánh giá là phù hợp "
            "với Job_Name."
        )
    )

    exp_bank: Literal[
        "Chưa có kinh nghiệm",
        "Dưới 1 năm kinh nghiệm",
        "Từ 1-3 năm kinh nghiệm",
        "Từ 3-5 năm kinh nghiệm",
        "Trên 5 năm kinh nghiệm",
    ] = Field(
        description=(
            "Chỉ tính kinh nghiệm tại Ngân hàng, Chứng khoán hoặc Bảo hiểm."
        )
    )

    skills: str = Field(
        description=(
            "Quét mục Skills/Technologies và Project. "
            "Nếu có nhiều loại thì chia rõ Tech Skills và Other Skills."
        )
    )


def extract_cv(text: str, job=None) -> dict:

    jobs = get_all_job_names()

    job_list = "\n".join(
        f"- {item}"
        for item in jobs
    )

    system_prompt = (
        "Bạn là chuyên gia HR cao cấp. "
        "Nhiệm vụ của bạn là bóc tách thông tin từ CV theo các quy tắc nghiêm ngặt sau:\n\n"

        "1. Xử lý Kinh nghiệm (EXP & EXP_Bank):\n"
        "- Bóc tách lịch sử làm việc thành danh sách có cấu trúc.\n"
        "- Đánh giá từng vị trí có Match với Job_Name mục tiêu hay không.\n"
        "- Chỉ cộng thời gian của các vị trí Match.\n"
        "- Với exp_bank chỉ tính các công ty thuộc Ngân hàng, Chứng khoán hoặc Bảo hiểm.\n\n"

        "2. Danh sách Job:\n"
        f"{job_list}\n\n"

        "Trường job_name chỉ được phép trả về đúng MỘT giá trị trong danh sách trên.\n"
        "Nếu CV dùng tên khác nhưng tương đương thì ánh xạ sang vị trí gần nhất.\n\n"

        "3. Quy tắc:\n"
        "- Không được suy diễn.\n"
        "- Không tự bổ sung thông tin.\n"
        "- Nếu không tìm thấy thì trả về giá trị phù hợp theo Schema.\n"
        "- Skills chia rõ Tech Skills và Other Skills nếu CV có nhiều nhóm kỹ năng.\n"
    )

    # Chỉ ép job khi người dùng chọn
    if job and job != "Auto Detect":
        system_prompt += (
            "\nCV này đã được chọn chuyên ngành.\n"
            f"Giá trị job_name PHẢI là '{job}'."
        )

    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"Nội dung văn bản CV cần xử lý:\n\n{text}",
            },
        ],
        text_format=CVStructure,
    )

    return response.output_parsed.model_dump()
