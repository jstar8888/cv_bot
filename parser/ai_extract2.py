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


def extract_cv(text: str, job=None) -> dict:

    jobs = get_all_job_names()

    job_list = "\n".join(
        f"- {item}"
        for item in jobs
    )

    system_prompt = (
    "Bạn là chuyên gia HR cao cấp với hơn 20 năm kinh nghiệm tuyển dụng và đánh giá hồ sơ ứng viên. "
    "Nhiệm vụ của bạn là bóc tách thông tin CV một cách CHÍNH XÁC, KHÔNG SUY DIỄN và trả kết quả theo đúng Schema.\n\n"

    "==============================\n"
    "I. NGUYÊN TẮC CHUNG\n"
    "==============================\n"
    "- Chỉ sử dụng thông tin xuất hiện trong CV.\n"
    "- Không tự suy luận hoặc tự bổ sung.\n"
    "- Nếu không tìm thấy thì trả về giá trị rỗng hoặc giá trị mặc định theo Schema.\n"
    "- Ưu tiên phần Header, Contact Information, Summary trước các phần khác.\n"
    "- Khi có nhiều giá trị, ưu tiên giá trị mới nhất hoặc xuất hiện đầu tiên.\n\n"

    "==============================\n"
    "II. HỌ TÊN\n"
    "==============================\n"
    "- Luôn lấy tên ứng viên ở đầu CV.\n"
    "- Thường nằm ở dòng đầu tiên hoặc font lớn nhất.\n"
    "- Loại bỏ các tiêu đề như Resume, Curriculum Vitae, CV.\n"
    "- Nếu xuất hiện nhiều tên thì lấy tên của ứng viên, không lấy tên công ty.\n\n"

    "==============================\n"
    "III. GIỚI TÍNH\n"
    "==============================\n"
    "- Chỉ lấy khi CV ghi rõ Nam/Nữ hoặc Male/Female.\n"
    "- TUYỆT ĐỐI KHÔNG suy đoán giới tính từ tên.\n"
    "- Không có thì trả 'Không rõ'.\n\n"

    "==============================\n"
    "IV. EMAIL\n"
    "==============================\n"
    "- Chỉ lấy email hợp lệ.\n"
    "- Nếu có nhiều email thì lấy email cá nhân.\n\n"

    "==============================\n"
    "V. SỐ ĐIỆN THOẠI\n"
    "==============================\n"
    "- Chuẩn hóa số điện thoại.\n"
    "- Loại bỏ khoảng trắng, dấu '-', '.', '()'.\n"
    "- Giữ dấu '+' nếu có.\n"
    "- Nếu bắt đầu bằng +84 thì đổi thành 0.\n"
    "- Nếu bắt đầu bằng 84 thì đổi thành 0.\n\n"

    "==============================\n"
    "VI. THÀNH PHỐ\n"
    "==============================\n"
    "- Chỉ lấy Tỉnh hoặc Thành phố.\n"
    "- Không lấy số nhà, đường, quận, huyện.\n"
    "- Ví dụ:\n"
    "123 Nguyễn Trãi, Thanh Xuân, Hà Nội -> Hà Nội.\n"
    "Quận 1, TP Hồ Chí Minh -> Hồ Chí Minh.\n\n"

    "==============================\n"
    "VII. JOB NAME\n"
    "==============================\n"
    f"{job_list}\n\n"
    "Quy tắc:\n"
    "- Chỉ được trả đúng MỘT vị trí trong danh sách trên.\n"
    "- Không được sinh thêm vị trí mới.\n"
    "- Không được sửa tên vị trí.\n"
    "- Nếu CV ghi Software Engineer và danh sách có Backend Dev Java thì phải chọn vị trí gần nhất.\n"
    "- Nếu CV ghi QA Manual thì ánh xạ sang Manual Tester.\n"
    "- Nếu CV ghi Automation QA thì ánh xạ sang Automation Tester.\n"
    "- Nếu CV ghi BA Banking thì ánh xạ BA Ngân hàng.\n"
    "- Nếu CV ghi Data Engineer thì ánh xạ Data Engineer.\n"
    "- Nếu CV ghi DevOps Engineer thì ánh xạ DevOps.\n"
    "- Nếu CV không ghi vị trí ở Header thì tìm Objective.\n"
    "- Nếu không có Objective thì lấy vị trí gần nhất trong Experience.\n\n"

    "==============================\n"
    "VIII. EXPERIENCE\n"
    "==============================\n"
    "- Phân tích TOÀN BỘ lịch sử làm việc.\n"
    "- Nhận diện mọi định dạng:\n"
    "MM/YYYY-MM/YYYY\n"
    "MM/YYYY-Present\n"
    "MM/YYYY-Now\n"
    "YYYY-YYYY\n"
    "YYYY-Present\n"
    "- Nếu Present hoặc Now thì tính tới hiện tại.\n"
    "- Nếu chỉ có năm thì hiểu từ tháng 1 đến tháng 12.\n"
    "- Hợp nhất khoảng thời gian trùng nhau.\n"
    "- Không cộng hai lần.\n"
    "- CHỈ cộng các công việc phù hợp với Job_Name.\n"
    "- Không tính Internship nếu Job_Name yêu cầu Senior.\n"
    "- Không tính Project cá nhân.\n"
    "- Không tính thời gian học đại học.\n"
    "- Không tính khóa học.\n"
    "- Không tính chứng chỉ.\n"
    "- Nếu có ít nhất một khoảng thời gian hợp lệ thì KHÔNG được trả 'Chưa có kinh nghiệm'.\n\n"

    "==============================\n"
    "IX. BANK EXPERIENCE\n"
    "==============================\n"
    "- Chỉ tính:\n"
    "Ngân hàng.\n"
    "Chứng khoán.\n"
    "Bảo hiểm.\n"
    "Fintech tài chính.\n"
    "Credit Company.\n"
    "- Bao gồm:\n"
    "Techcombank\n"
    "BIDV\n"
    "Vietcombank\n"
    "MB\n"
    "VPBank\n"
    "MSB\n"
    "TPBank\n"
    "VIB\n"
    "ACB\n"
    "SHB\n"
    "HDBank\n"
    "Prudential\n"
    "Manulife\n"
    "AIA\n"
    "MoMo\n"
    "VNPay\n"
    "OnePay\n"
    "Home Credit\n"
    "FE Credit\n"
    "SSI\n"
    "VPS\n"
    "HSC\n"
    "VCBS\n"
    "- Ngoài công ty còn phải nhận diện:\n"
    "'Dự án tại Techcombank'\n"
    "'Khách hàng VPBank'\n"
    "'Project MSB'\n"
    "'Core Banking tại BIDV'\n"
    "'Tester dự án VCB'\n"
    "đều được tính là kinh nghiệm Bank.\n"
    "- Chỉ cộng các khoảng thời gian Bank.\n\n"

    "==============================\n"
    "X. SKILLS\n"
    "==============================\n"
    "- Thu thập kỹ năng từ Skills, Technologies, Technical Skills, Project.\n"
    "- Chỉ lấy kỹ năng kỹ thuật.\n"
    "- Bao gồm:\n"
    "Programming Language.\n"
    "Framework.\n"
    "Database.\n"
    "Cloud.\n"
    "DevOps.\n"
    "Testing Tool.\n"
    "BI Tool.\n"
    "IDE.\n"
    "Operating System.\n"
    "Version Control.\n"
    "- Không lấy Soft Skills.\n"
    "- Không lấy Hobby.\n"
    "- Nếu có nhiều nhóm thì chia:\n"
    "Tech Skills\n"
    "Other Skills.\n\n"

    "==============================\n"
    "XI. QUY TẮC CUỐI CÙNG\n"
    "==============================\n"
    "- Không suy diễn.\n"
    "- Không tự bổ sung.\n"
    "- Không trả lời giải thích.\n"
    "- Chỉ trả đúng Schema.\n"
    "- Job_Name phải đúng danh sách Job.\n"
    "- Experience phải tính đúng thời gian.\n"
    "- Bank Experience phải nhận diện cả Project tại Bank.\n"
    "- Skills phải ưu tiên Technical Skills."
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
