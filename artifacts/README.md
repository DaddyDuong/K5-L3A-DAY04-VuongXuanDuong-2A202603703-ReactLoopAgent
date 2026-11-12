# Bằng chứng thực hành

- `agent_before.py`: agent thực sự dùng trong `../eval_before.json`.
- `a7_before_evidence.json`: trích nguyên answer, trace và grade A7 từ lượt trước.
- `agent_after_attempts.py`: phiên bản cải tiến đầu tiên, trước khi bổ sung xử lý JSON hỏng và không lặp payload injection.
- `eval_after_unscored.json`: lần thử sau đầu tiên, 21/22 case được chấm, A1 lỗi JSONDecodeError.
- `eval_after_unscored_2.json`: lần thử sau thứ hai, 20/22 case được chấm, A3/H7 lỗi JSONDecodeError; H5 lặp payload injection.
- `eval_after_unscored_3.json`: lần thử sau thứ ba, agent hoàn tất cả bộ nhưng judge E6 thiếu trường giải thích/đề xuất.
- `comparison.json`: thống kê hai báo cáo đầy đủ bằng script compare_evals.py.
- `baseline_manifest.json`: SHA-256 của snapshot, bộ case, scenario, grading, rubric và các bản agent lưu lại.

Ba báo cáo `unscored` được giữ để công bố thất bại; không dùng để ghép hoặc thay điểm trong báo cáo cuối. Các file eval được tạo bởi runner, không sửa điểm, answer hay trace bằng tay.

Tái chạy baseline với adapter/provider hiện tại (API có tính phí):

```bash
source .env
python3 scripts/run_baseline_evals.py --workers 4 --max-steps 8 --output eval_before_reproduced.json
```

Tái chạy bản cuối:

```bash
source .env
python3 evals/run_evals.py --workers 4 --max-steps 8 --output eval_after_reproduced.json
```

Giữ nguyên agent/judge model, endpoint và các biến JUDGE_PROVIDER/JUDGE_MODEL như NOTES.md. Endpoint có thể trả kết quả khác giữa các lượt. Adapter cuối có retry giới hạn đối với HTTP body sai JSON; adapter ở lượt baseline gốc chưa có retry này. Không có thay đổi dữ liệu snapshot hoặc bộ chấm.
