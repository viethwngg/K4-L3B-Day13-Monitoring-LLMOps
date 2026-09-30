# Alerts và runbook

Mỗi alert dưới đây dựa trên triệu chứng mà người dùng quan sát được hoặc trên SLO. Quy trình điều tra luôn đi theo thứ tự Metrics → Logs → Traces.

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: P95 của `response_sent.latency_ms`, ngưỡng SLO 3000 ms.
- Điều kiện: P95 lớn hơn 3000 ms liên tục trong 5 phút.
- Ảnh hưởng: phần đuôi request chậm, người dùng phải chờ lâu hơn để nhận câu trả lời.
- Kiểm tra:
  1. Xác nhận P50/P95/P99 và TTFT trên panel Latency, ghi lại cửa sổ sự cố.
  2. Lọc `response_sent` có `latency_ms > 3000`, chọn một `correlation_id` đại diện.
  3. Mở trace cùng `correlation_id`, so sánh thời lượng `retrieval` và `generation`.
- Mitigation: tắt practice incident nếu đang bật; nếu generation tăng sau đổi prompt thì rollback label `production`; nếu retrieval chậm thì giảm tải và khôi phục dependency liên quan.
- Owner: `student-2A202602600`

## Alert 2

- Tên: `HighRequestErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỷ lệ `request_failed / request_received`, guardrail tối đa 2%.
- Điều kiện: error rate lớn hơn 2% liên tục trong 5 phút.
- Ảnh hưởng: request không trả về câu trả lời thành công.
- Kiểm tra:
  1. Xác nhận error rate và nhóm `error_type` trên panel Errors.
  2. Lọc `request_failed` trong cửa sổ cảnh báo và chọn một `correlation_id`.
  3. Mở trace tương ứng để xác định observation lỗi và đối chiếu deployment/prompt gần nhất.
- Mitigation: rollback thay đổi gần nhất nếu có quan hệ thời gian rõ ràng; khôi phục dependency lỗi hoặc chuyển sang fallback an toàn.
- Owner: `student-2A202602600`

## Alert 3

- Tên: `LowRetrievalSuccessRate`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỷ lệ thành công của tool `retrieval`, guardrail tối thiểu 90%.
- Điều kiện: retrieval success rate dưới 90% liên tục trong 10 phút.
- Ảnh hưởng: câu trả lời thiếu context hoặc request thất bại, làm giảm độ chính xác.
- Kiểm tra:
  1. Xác nhận retrieval success và error breakdown trên panel Errors.
  2. Lọc log có `tool_name=retrieval` và `tool_success=false`, lấy `correlation_id` đại diện.
  3. Mở trace tương ứng, kiểm tra trạng thái span `retrieval` và thời gian phản hồi dependency.
- Mitigation: chuyển sang context fallback đã kiểm soát, giảm concurrency nếu dependency quá tải và khôi phục kết nối tới vector store.
- Owner: `student-2A202602600`
