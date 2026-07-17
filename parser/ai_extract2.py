import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Literal
from service.jobs_service import get_all_job_names

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class CVStructure(BaseModel):
    full_name: str = Field(
        description=(
            "Họ tên ứng viên. Nguyên tắc: Nằm ở dòng đầu tiên hoặc font chữ lớn nhất ở đầu trang 1. "
            "Loại trừ các từ tiêu đề như 'Curriculum Vitae', 'Resume', 'CV'. Lấy chuỗi Title Case hoặc UPPER CASE ở top header."
        )
    )

    gender: Literal["Nam", "Nữ", "Không rõ"] = Field(
        description="Tìm từ khóa định danh: 'Male'/'Female'/'Nam'/'Nữ'. Không thấy thì trả về 'Không rõ', TUYỆT ĐỐI không đoán mò dựa trên tên."
    )

    email: str = Field(
        description="Địa chỉ email chuẩn trích xuất theo định dạng Regex [string]@[domain].[com/vn/...]."
    )

    phone: str = Field(
        description="Số điện thoại (độ dài 10-15 ký tự). Logic làm sạch: Loại bỏ toàn bộ khoảng trắng, dấu gạch -, dấu ngoặc (), chỉ giữ lại số và dấu + ở đầu."
    )

    city: str = Field(
        description="Thành phố/Tỉnh thành tại Việt Nam. Ưu tiên tìm ở Header/Contact Info, nếu không thấy mới tìm trong phần Experience gần nhất."
    )

    job_name: str = Field(
        description="Vị trí ứng tuyển thích hợp. Tìm dòng mô tả ngắn ngay dưới tên hoặc trong phần Summary, sau đó ánh xạ vào danh sách công ty."
    )

    exp: Literal[
        "Chưa có kinh nghiệm",
        "Dưới 1 năm kinh nghiệm",
        "Từ 1-3 năm kinh nghiệm",
        "Từ 3-5 năm kinh nghiệm",
        "Trên 5 năm kinh nghiệm"
    ] = Field(
        description="Tổng thời gian của tất cả các vị trí làm việc ĐÃ ĐÁNH GIÁ là phù hợp (Match) với Job_Name mục tiêu."
    )

    exp_bank: Literal[
        "Chưa có kinh nghiệm",
        "Dưới 1 năm kinh nghiệm",
        "Từ 1-3 năm kinh nghiệm",
        "Từ 3-5 năm kinh nghiệm",
        "Trên 5 năm kinh nghiệm"
    ] = Field(
        description="Tổng thời gian làm việc CHỈ TÍNH riêng cho các tổ chức Ngân hàng (Bank), Chứng khoán, hoặc Bảo hiểm."
    )

    skills: str = Field(
        description="Quét dưới các Section Header (SKILLS, TECHNOLOGIES...) và trong mô tả dự án. So khớp từ điển công nghệ, trả về dạng chuỗi cách nhau bằng dấu phẩy."
    )


def extract_cv(text: str, job=None) -> dict:

    jobs = get_all_job_names()

    job_list = "\n".join(
        f"- {item}"
        for item in jobs
    )

    system_prompt = (
        "Bạn là chuyên gia HR cao cấp. Nhiệm vụ của bạn là bóc tách thông tin từ CV theo các quy tắc nghiêm ngặt sau:\n"
        "1. Xử lý Kinh nghiệm (EXP & EXP_Bank):\n"
        "   - Bóc tách lịch sử làm việc thành một danh sách có cấu trúc cấu thành từ các mốc thời gian.\n"
        "   - Đánh giá từng vị trí xem có thực sự 'Match' với Job_Name mục tiêu hay không.\n"
        "   - Tính toán chính xác tổng thời gian (năm/tháng) của các vị trí hợp lệ để đưa ra kết quả phân loại.\n"
        "   - Với 'exp_bank', áp dụng logic tương tự nhưng loại trừ toàn bộ các công ty không thuộc ngành Ngân hàng, Bảo hiểm, Chứng khoán.\n"
        f"2. Vị trí ứng tuyển:\n{job_list}\n"
        "Trường job_name chỉ được phép trả về đúng MỘT vị trí trong danh sách trên.\n"
        "Nếu CV sử dụng tên vị trí khác nhưng tương đương về ý nghĩa thì ánh xạ sang vị trí phù hợp nhất trong danh sách.\n"
        "3. Một vài lưu ý quan trọng:\n"
        "   - Không được tự ý đoán mò thông tin nếu không tìm thấy trong CV.\n"
        "   - Không được thêm bất kỳ thông tin nào ngoài những gì có trong CV.\n"
        "   - Trong mục skills chia rõ làm Tech skills và Other skill nếu cv có nhiều loại skill.\n"
        "4. Định dạng dữ liệu đầu ra hoàn toàn sạch, tuân thủ 100% JSON Schema được cung cấp.\n"
    )

    if job != "Auto Detect":
        system_prompt += (
            "CV này đã lựa chọn chuyên ngành rồi, "
            "không cần dự đoán job_name nữa. "
            f"Giá trị job_name phải là '{job}'."
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
        temperature=0.1,
    )

    return response.output_parsed.model_dump()