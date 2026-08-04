import os
import json
from typing import Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from service.jobs_service import get_all_job_names

load_dotenv()
client = genai.Client()




class CVStructure(BaseModel):
    full_name: str = Field(
        description=(
            "Họ và tên đầy đủ của ứng viên. "
            "Ưu tiên lấy ở phần đầu CV, thường là dòng đầu tiên hoặc dòng có cỡ chữ lớn nhất. "
            "Loại bỏ các tiêu đề như 'CV', 'Resume', 'Curriculum Vitae'. "
            "Không lấy tên công ty, tên trường học hoặc tên người tham chiếu. "
            "Nếu tên không có dấu nhưng có thể xác định rõ thì chuyển về tiếng Việt có dấu. "
            "Nếu có nhiều tên thì chọn tên của ứng viên."
        )
    )
    
    gender: Literal["Nam", "Nữ", "Không rõ"] = Field(
        description=(
            "Chỉ trả về 'Nam', 'Nữ' hoặc 'Không rõ'. "
            "Ưu tiên tìm các trường 'Gender', 'Giới tính', 'Male', 'Female', 'Nam', 'Nữ'. "
            "Nếu CV không ghi rõ thì trả về 'Không rõ'. "
            "Không được suy đoán giới tính dựa trên tên."
        )
    )
    
    email: str = Field(
        description=(
            "Địa chỉ email của ứng viên. "
            "Ưu tiên email cá nhân. "
            "Nếu có nhiều email thì lấy email đầu tiên dùng để liên hệ. "
            "Nếu không có thì trả về chuỗi rỗng."
        )
    )
    
    phone: str = Field(
        description=(
            "Số điện thoại của ứng viên. "
            "Loại bỏ khoảng trắng, dấu '-', '.', '()'. "
            "Nếu bắt đầu bằng '+84' thì chuyển thành '0'. "
            "Nếu bắt đầu bằng '84' thì chuyển thành '0'. "
            "Ví dụ: +84912345678 -> 0912345678. "
            "Nếu không có thì trả về chuỗi rỗng."
        )
    )
    
    city: str = Field(
        description=(
            "Chỉ lấy tên tỉnh hoặc thành phố nơi ở của ứng viên. "
            "Ưu tiên mục Address hoặc Contact Information. "
            "Không lấy số nhà, đường, phường, quận. "
            "Ví dụ: '123 Nguyễn Trãi, Thanh Xuân, Hà Nội' chỉ trả về 'Hà Nội'. "
            "Nếu không có thì trả về chuỗi rỗng."
        )
    )
    
    job_name: str = Field(
        description=(
            "Vị trí ứng tuyển của ứng viên. "
            "BẮT BUỘC phải ánh xạ chính xác về MỘT vị trí trong danh sách Job được cung cấp. "
            "Không được sinh thêm vị trí mới. "
            "Ưu tiên tìm ở Header, Objective, Career Objective, Desired Position. "
            "Nếu không có thì lấy chức danh gần nhất trong Experience rồi ánh xạ sang danh sách Job."
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
            "Tổng số năm kinh nghiệm phù hợp với job_name. "
            "Đọc toàn bộ mục Experience hoặc Work Experience. "
            "Nhận diện mọi khoảng thời gian dạng MM/YYYY-MM/YYYY, YYYY-YYYY, Present hoặc Now. "
            "Nếu khoảng thời gian chồng lắp thì hợp nhất và không tính trùng. "
            "Chỉ cộng các công việc phù hợp với job_name. "
            "Không tính thời gian học đại học, thực hành, khóa học hoặc project cá nhân nếu không phải kinh nghiệm làm việc."
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
            "Chỉ tính kinh nghiệm tại Ngân hàng, Công ty Tài chính, Chứng khoán, Bảo hiểm hoặc Fintech. "
            "Bao gồm cả trường hợp ứng viên làm dự án cho ngân hàng như 'Project tại Techcombank', "
            "'Khách hàng BIDV', 'Core Banking tại VPBank', 'Tester dự án MSB'. "
            "Không tính các công ty CNTT thông thường nếu không có khách hàng hoặc dự án thuộc lĩnh vực tài chính."
        )
    )
    
    skills: str = Field(
        description=(
            "Trích xuất kỹ năng kỹ thuật của ứng viên. "
            "Ưu tiên mục Skills, Technical Skills, Technologies, Tech Stack hoặc Project. "
            "Chỉ lấy công nghệ, framework, database, cloud, ngôn ngữ lập trình, công cụ và nền tảng. "
            "Không lấy kỹ năng mềm như Teamwork, Communication, Leadership. "
            "Nếu CV có nhiều nhóm thì gộp thành một danh sách kỹ năng kỹ thuật."
        )
    )
def extract_cv(text: str, job = None) -> dict:
    # Định nghĩa danh sách các vị trí tuyển dụng chính thức của công ty
    jobs = get_all_job_names()

    job_list = "\n".join(
        f"- {job}"
        for job in jobs
    )

    # Đưa các nguyên tắc vận hành cốt lõi vào system_instruction để ép AI suy luận đúng quy trình
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
        "   - Không được tự ý đoán mò thông tin nếu không tìm thấy trong CV. Hãy tuân thủ theo mô tả ''.\n"
        "   - Không được thêm bất kỳ thông tin nào ngoài những gì có trong CV.\n"
        "   - Trong mục skills chia rõ làm Tech skills và Other skill nếu cv có nhiều loại skill.\n"
        "4. Định dạng dữ liệu đầu ra hoàn toàn sạch, tuân thủ 100% JSON Schema được cung cấp.\n"
    )

    if  job != "Auto Detect":
        system_prompt += "Cv này đã lựa chọn chuyên ngành rồi không cần dự đoán job_name nữa."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Nội dung văn bản CV cần xử lý:\n\n{text}",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=CVStructure,
            temperature=0.1, # Giữ mức nhiệt độ thấp để AI tuân thủ quy tắc logic tuyệt đối
        ),
    )
    return json.loads(response.text)
