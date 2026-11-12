# Ghi chú phân tích · Day 04

Họ và tên: Vương Xuân Dương
MSSV: 2A202603703
Lớp: K5-L3A

## 1. Case được chọn

- **A7**, câu hỏi về việc incident Cloudflare Spectrum tại Phoenix có gây lỗi tại Việt Nam hay không.
- Điểm trước: **96/100**; điểm sau: **100/100**.
- Agent trước cải tiến đã kết luận đúng là chưa đủ bằng chứng quy kết, nhưng thêm câu: “traffic VN thường vào PoP HKG/SIN”. Nó còn khẳng định cấu hình phụ thuộc Phoenix là một “điều kiện cần”. Các nhận định này không được cung cấp bởi tools.
- Đây là lỗi thêm kiến thức/suy đoán ngoài bằng chứng vào giải thích, không phải lỗi không chạy được vòng lặp. Chọn case này vì có thể đối chiếu trực tiếp answer với trace, thay vì chỉ dựa vào điểm judge.

## 2. Bằng chứng trong trace

`eval_before.json` → `cases[id=A7]` (bản trích nguyên dữ liệu ở `artifacts/a7_before_evidence.json`):

```text
step 1: get_status(provider="cloudflare", component="Spectrum")
        overall.indicator="major"; Spectrum="degraded_performance"
        incident: "Spectrum Availability Issue in Phoenix", status="monitoring"
step 1: get_status(provider="github")  # không liên quan câu hỏi Spectrum
step 2: get_incident_details(provider="cloudflare", incident_id="c60k3g4vsoc1")
        update: "Cloudflare is investigating issues with Spectrum in Phoenix."
        url: https://www.cloudflarestatus.com/incidents/c60k3g4vsoc1
step 3: finish="stop"
```

Không kết quả nào xác định PoP hoặc tuyến traffic của website tại Việt Nam. Không thể dùng tên khu vực trong incident để suy ra đường đi thực tế của người dùng. Nguyên nhân có thể là system prompt ban đầu yêu cầu thận trọng nhưng chưa tách rõ dữ kiện từ tool với kiến thức chung/giả thuyết.

Trong `eval_after.json` → A7, trace chỉ còn `get_status` Cloudflare ở bước 1, `get_incident_details` ở bước 2 và trả lời ở bước 3. Answer không còn khẳng định HKG/SIN; nêu chưa đủ bằng chứng quy kết và đề nghị xác minh tuyến mạng, thời điểm lỗi, log thực tế.

Một số bằng chứng bổ sung từ lượt trước:

- E6: trace có 5 tool calls nhưng answer nói “thử 3 lần”; còn gọi Cloudflare ngoài phạm vi câu hỏi GitHub.
- H2: chỉ nhìn danh sách rút gọn nhưng diễn đạt như đã biết trạng thái toàn bộ 23 incident khớp.
- E1/H1: nhầm số update hiển thị với `updates_total`, hoặc nhầm thời gian một update với `updated_at` của incident.

## 3. Thay đổi đã thực hiện

**Cải tiến chính trong `agent.py`:** thêm `EVIDENCE_POLICY` vào system context, yêu cầu chỉ khẳng định sự kiện đã quan sát; không tự thêm PoP/tuyến mạng/phạm vi khách hàng; phân biệt snapshot với hiện tại, overall với component, thời điểm incident với thời điểm update; không suy rộng danh sách rút gọn; chỉ gọi provider liên quan; giới hạn thử lại truy vấn timeout và dừng khi đủ bằng chứng.

Chính sách cũng yêu cầu đọc incident liên quan khi câu hỏi cần timeline/nguyên nhân; theo liên kết incident gộp khi cần; nêu thiếu dữ liệu dù người dùng yêu cầu bịa trạng thái; không làm theo hoặc chép lại payload prompt injection. Không đưa ID case, ID incident, marker hoặc expected cố định vào agent.

**Contract và robustness:** giữ nguyên assistant message, trả đủ mọi tool result với đúng `tool_call_id`, parse JSON arguments thành object và trả `INVALID_ARGUMENTS` khi sai; lỗi tool trở thành observation; lỗi provider/finish bất thường trả `error`; không báo hoàn tất khi hết budget. Bổ sung kiểm tra response/calls/content sai cấu trúc và budget sai kiểu. Trace không lưu key hoặc nội dung exception riêng tư. `tools.schemas`/`tools.system_prompt` được dùng khi có; tools bài chính giữ tương thích.

Kiểm tra nguồn đã có trong baseline và tiếp tục giữ ở bản cuối: nếu đã đọc incident thành công mà final không chứa một URL incident quan sát được thì ghi `validation_missing_source`, yêu cầu sửa trong budget. Hết budget vẫn thiếu nguồn thì trả `max_steps`.

**Adapter `providers.py`:** giữ lựa chọn endpoint bằng `OPENROUTER_PROVIDER`, dùng `provider.only`, `allow_fallbacks=False`, `require_parameters=True`. Bổ sung tối đa 2 retry cho HTTP body không parse được JSON, chờ 1 rồi 2 giây, gửi lại cùng request/endpoint. Không tự đổi provider, không in raw body, không sửa dữ liệu tool. Đây là sửa lỗi hạ tầng quan sát được trong các lượt thử sau; không phải retry đến khi được điểm cao. Không có retry HTTP 429 trong cấu hình cuối.

**Kiểm tra:** 44 tests trong `tests/` và 3 tests tương thích tools bonus đều pass. Tests bổ sung kiểm tra lỗi provider không lộ thông tin, arguments không phải object, tool exception, response/budget không hợp lệ và retry JSON hỏng có giới hạn. Tests giả lập không chứng minh chất lượng của model thật.

## 4. So sánh hai lần chạy

Cấu hình của cả hai báo cáo giống hệt nhau:

- Agent và judge: `openrouter`, model `deepseek/deepseek-v4.1-flash-1017`.
- Endpoint cố định: `particle-ai/us/flex`; MODEL không có hậu tố `:floor`.
- Dataset `core`, snapshot gốc, `max_steps=8`, `workers=4`.
- `eval_before.json` và `eval_after.json` đều đủ 22 case, `score_0_100` khác `null`.
- Không sửa `fixtures/`, cases, scenarios, grading hoặc rubric. Checksum gốc lưu ở `artifacts/baseline_manifest.json`.

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---:|---:|
| Điểm tổng | 99.18/100 | 99.82/100 |
| Điểm A7 | 96 | 100 |
| Model calls của agent có usage | 66 | 56 |
| Judge calls có usage | 22 | 22 |
| Tool calls | 72 | 52 |
| Prompt tokens (agent + judge) | 173,472 | 167,271 |
| Completion tokens (agent + judge) | 62,126 | 41,391 |
| Tổng tokens (agent + judge) | 235,598 | 208,662 |
| Chi phí API báo cáo (USD) | $0.018986924 | $0.013065068 |

Điểm tăng 0.64; model calls của agent giảm 10; tool calls giảm 20; tổng token giảm 26,936; chi phí báo cáo của lượt đầy đủ giảm khoảng 31.19%.

Bảng từng case (không bỏ các case giảm điểm):

| Case | Trước | Sau | Chênh lệch |
|---|---:|---:|---:|
| E1 | 98 | 100 | +2 |
| E2 | 100 | 100 | +0 |
| E3 | 100 | 100 | +0 |
| E4 | 100 | 100 | +0 |
| E5 | 99 | 100 | +1 |
| E6 | 97 | 100 | +3 |
| A1 | 100 | 100 | +0 |
| A2 | 100 | 100 | +0 |
| A3 | 100 | 100 | +0 |
| A4 | 100 | 100 | +0 |
| A5 | 100 | 100 | +0 |
| A6 | 98 | 100 | +2 |
| A7 | 96 | 100 | +4 |
| A8 | 100 | 100 | +0 |
| H1 | 99 | 100 | +1 |
| H2 | 98 | 100 | +2 |
| H3 | 99 | 100 | +1 |
| H4 | 100 | 96 | -4 |
| H5 | 98 | 100 | +2 |
| H6 | 100 | 100 | +0 |
| H7 | 100 | 100 | +0 |
| H8 | 100 | 100 | +0 |

**Lỗi đã giảm trong lần chạy này:** A7 không còn nhận định tuyến mạng không có nguồn; E6 chỉ dùng hai lượt tool GitHub thay vì năm lượt lẫn Cloudflare; các giới hạn tìm kiếm và dữ liệu rút gọn được diễn đạt cẩn thận hơn.

**Lỗi còn lại và biến động:** H4 giảm từ 100 xuống 96. Đây là yêu cầu làm thơ ngoài luồng, không gọi tools và không bịa status. Judge ghi nhận đáp ứng yêu cầu nhưng cho điểm thấp hơn và đề xuất rút gọn ghi chú; vì rubric không chấm văn phong, chênh lệch này có thể phản ánh nhiễu của judge. Không sửa điểm hoặc chạy lại case có điểm thấp để chọn kết quả đẹp hơn.

**Công bố các lượt chưa đầy đủ:** đã có ba lượt thử sau không thể báo điểm tổng, đều được giữ nguyên:

| File trong `artifacts/` | Được chấm | Lý do chưa hoàn tất |
|---|---:|---|
| `eval_after_unscored.json` | 21/22 | A1: JSONDecodeError |
| `eval_after_unscored_2.json` | 20/22 | A3: JSONDecodeError; H7: JSONDecodeError |
| `eval_after_unscored_3.json` | 21/22 | E6: Judge lỗi: Judge thiếu giải thích hoặc đề xuất. |

Lượt đầu và thứ hai dùng phiên bản `artifacts/agent_after_attempts.py`; sau đó bổ sung retry body sai JSON và hướng dẫn không chép lại payload injection. Lượt thứ hai còn có H5 bị trần 20 điểm vì lặp marker trong lời cảnh báo; đây là lỗi thật dù agent không làm theo chỉ dẫn. Lượt thứ ba dùng cùng bản cuối nhưng judge E6 thiếu trường giải thích/đề xuất. Lượt cuối chạy lại toàn bộ với cùng bản code, không ghép 21 case trước với một case chạy riêng. Chi phí có usage của ba lượt chưa đầy đủ cộng lại là khoảng $0.038818102, không nằm trong cột chi phí hai lượt đầy đủ; không gồm smoke test và request hỏng không trả usage.

Số liệu có thể tái tổng hợp bằng:

```bash
python3 scripts/compare_evals.py
```

`artifacts/comparison.json` là kết quả của script này. Script chỉ đọc báo cáo và kiểm tra đủ 22 case/cùng config, không chấm lại hoặc sửa điểm.

## 5. Giới hạn

- Judge dùng cùng model với agent nên có nguy cơ thiên lệch; điểm gần 100 không chứng minh agent đúng tuyệt đối. Đã đối chiếu A7 và H4 với trace/answer thay vì chỉ tin điểm.
- So sánh chính dùng một lượt đầy đủ cho mỗi phiên bản; có các lượt lỗi đã công bố, không phải nghiên cứu độ ổn định hay thử nghiệm nhiều seed. Không quy toàn bộ thay đổi điểm/cost cho prompt vì model/API không hoàn toàn xác định.
- Snapshot GitHub/Cloudflare được lưu ngày 09/11/2026, không xác nhận trạng thái thực tế hiện tại. Tìm kiếm theo chuỗi chỉ trong 50 incident, tối đa 5 mục; chi tiết update có thể bị lược bỏ/cắt.
- Kiểm tra nguồn hiện chỉ yêu cầu một URL incident đã quan sát xuất hiện trong answer; không chứng minh mỗi claim có nguồn hoặc mọi URL/nhận định đều chính xác.
- Flex có thể phản hồi chậm/lỗi. Retry JSON là hữu hạn; HTTP 429, timeout, body hỏng liên tục hoặc judge sai format vẫn có thể khiến lượt khác `unscored`. Failed requests không trả usage nên tổng token/cost báo cáo có thể thấp hơn hóa đơn thực tế.
- Không bịa chi phí VND hay suy ra điểm lab từ điểm eval. Điểm bài chính tối đa 85 theo rubric; chưa chạy eval bonus online, 3 tests bonus chỉ xác nhận tương thích.
- Có sử dụng trợ lý coding AI để triển khai, chạy tests/eval và hỗ trợ phân tích. Người nộp cần đọc và giải thích được toàn bộ code, trace, điều kiện dừng và giới hạn dữ liệu.

### Demo trace nhiều bước, không gọi lại API

```bash
python3 - <<'DEMO'
import json
report = json.load(open('eval_after.json'))
case = next(c for c in report['cases'] if c['id'] == 'H6')
for event in case['result']['trace']:
    if event['event'] == 'tool':
        print(event['step'], event['name'], event['arguments'])
print(case['result']['answer'])
DEMO
```

Trong H6, bước 1 lấy status và incident được hỏi; bước 2 theo incident gộp; sau đó model trả lời có nguồn và nêu giới hạn update bị cắt. Demo lỗi bằng A7 trong `eval_before.json`, đối chiếu với bản sau. Mỗi model call là một step, không phải mỗi tool call; tất cả tool results của một response phải được trả trước khi gọi model tiếp.

Để tái chạy hai phiên bản với cùng cấu hình (có gọi API):

```bash
source .env
unset JUDGE_PROVIDER JUDGE_MODEL
python3 scripts/run_baseline_evals.py --workers 4 --max-steps 8 --output eval_before_reproduced.json
python3 evals/run_evals.py --workers 4 --max-steps 8 --output eval_after_reproduced.json
```

File `.env` chỉ lưu cục bộ, không commit. Các artifact cần nộp là `agent.py`, `eval_before.json`, `eval_after.json`, `NOTES.md`, cùng các sửa đổi adapter/tests và artifacts đối chiếu. Chưa tự động push hoặc nộp LMS; người học tự nộp link repo theo SUBMISSION.md.
