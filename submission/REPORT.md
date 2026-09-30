# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đàm Việt Hưng
- **MSSV:** 2A202602600
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/viethwngg/K4-L3B-Day13-Monitoring-LLMOps
- **Commit SHA cuối:** **[CẦN ĐIỀN: `git rev-parse HEAD` trên commit nộp cuối]**
- **Challenge ID:** **[CẦN ĐIỀN từ output `python scripts/load_test.py --challenge ...`]**
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-02600`

## 2. Evidence index

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.txt` |
| Log validator | `evidence/02-log-validator.txt` |
| Dashboard validator | `evidence/03-dashboard-validator.txt` |
| Structured log | `evidence/04-structured-log.txt` |
| PII redaction | `evidence/05-pii-redaction.txt` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata (`lab-agent-run`) | `evidence/08a-trace-metadata.png` |
| Generation detail | `evidence/08b-generation.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` *(hoặc `11a/11b/11c` nếu chia nhiều ảnh)* |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

> Các giá trị định lượng bên dưới phải lấy từ **evidence runtime thực tế của commit cuối**. Không nên tự suy đoán số liệu từ source code.

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | **[CẦN ĐIỀN baseline]** | **[CẦN ĐIỀN từ `evidence/02-log-validator.txt`]** | Mục tiêu: schema JSON hợp lệ, correlation ID được truyền, enrichment đầy đủ và không còn PII thô. |
| `validate_dashboard.py` | **[CẦN ĐIỀN baseline]** | **[CẦN ĐIỀN từ `evidence/03-dashboard-validator.txt`]** | Dashboard contract hiện có đúng 6 panel: latency, traffic, errors, cost, tokens, quality. |
| `pytest` | **[CẦN ĐIỀN baseline]** | **[CẦN ĐIỀN từ `evidence/01-pytest.txt`]** | Ghi đúng số test pass/fail của commit cuối. |
| Số traces hợp lệ | **[CẦN ĐIỀN]** | **[CẦN ĐIỀN từ `evidence/06-trace-list.png`]** | Yêu cầu bài: ít nhất 10 traces trong project Langfuse cá nhân. |
| Số PII leak | **[CẦN ĐIỀN baseline]** | **[CẦN ĐIỀN từ validator]** | Mục tiêu cuối là `0`. |
| Latency P95 / TTFT P95 | **[CẦN ĐIỀN]** | **[CẦN ĐIỀN từ dashboard/log]** | Đơn vị ms; panel latency có P50/P95/P99 và TTFT P95. |
| Retrieval success rate | **[CẦN ĐIỀN]** | **[CẦN ĐIỀN từ dashboard/log]** | Guardrail cấu hình tối thiểu 90%. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware `CorrelationIdMiddleware` xóa context cũ ở đầu request, đọc header `x-request-id` và chỉ chấp nhận dạng `req-<8 ký tự hex>`. Nếu header không hợp lệ hoặc không có, hệ thống sinh ID mới bằng `uuid.uuid4().hex[:8]`, bind vào `structlog.contextvars`, lưu tại `request.state.correlation_id`, truyền vào `LabAgent.run(...)`, sau đó trả lại qua response header `x-request-id`. Header `x-response-time-ms` cũng được ghi để hỗ trợ quan sát latency.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`, cùng các field vận hành như `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`, `error_type` và các preview đã được rút gọn/scrub. `user_id` không được ghi thô mà được SHA-256 rồi lấy 12 ký tự đầu.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trong pipeline `structlog` **trước** `JsonlFileProcessor` và trước JSON renderer cuối. Hàm scrub đi đệ quy qua string, mapping, list và tuple. Các pattern hiện được che gồm email, số điện thoại Việt Nam, CCCD 12 số, thẻ thanh toán, passport và chuỗi địa chỉ có nhãn. Preview message/answer còn được đi qua `summarize_text()` để scrub rồi giới hạn độ dài.
- **Cách kiểm chứng kết quả:** Chạy workload sau khi xóa/đổi tên log cũ, sau đó chạy `python scripts/validate_logs.py`. Validator đọc toàn bộ `data/logs.jsonl`, kiểm tra field bắt buộc/enrichment, số correlation ID duy nhất và tự quét PII độc lập. Evidence dùng `evidence/02-log-validator.txt`, `evidence/04-structured-log.txt` và `evidence/05-pii-redaction.txt`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Tôi dùng project Langfuse `day13-k4-l3b-02600`, chạy workload từ repo cá nhân và đối chiếu `correlation_id` giữa structured log với metadata của trace. Danh sách trace phải thể hiện ít nhất 10 request do workload của tôi tạo và không dùng evidence của project/lớp khác.
- **Cấu trúc root/retrieval/generation observations:** Cây trace được tổ chức theo dạng `day13-agent-request` → `lab-agent-run` → `retrieval` + `generation`. `lab-agent-run` là agent observation; `retrieval` là retriever/span; `generation` là generation observation có model, usage token và cost. Root agent tắt capture raw input/output để giảm nguy cơ lộ PII; phần cần quan sát dùng preview đã scrub và metadata an toàn.
- **Cách nối trace với log:** `correlation_id` được bind từ middleware, truyền vào `LabAgent.run()` và ghi vào metadata của trace/retrieval/generation. Khi điều tra, tôi lấy một `correlation_id` từ log rồi tìm trace có cùng ID để xác định span chậm hoặc lỗi.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** `v1` với label `baseline`; `production` ban đầu trỏ về v1.
- **Version/label candidate:** `v2` với label `candidate`; khi kiểm thử promote, `production` được chuyển tạm sang v2.
- **Trace ID của mỗi version:** Baseline v1: **[CẦN ĐIỀN trace ID từ Langfuse]**; Candidate v2: **[CẦN ĐIỀN trace ID từ Langfuse]**.
- **Cách promote và rollback `production`:** Ứng dụng lấy prompt theo `LANGFUSE_PROMPT_NAME=day13-chat` và `LANGFUSE_PROMPT_LABEL=production`, nên không cần đổi code khi đổi version. Tôi promote bằng cách chuyển label `production` từ v1 sang v2, chạy request để tạo trace chứng minh version mới, sau đó rollback bằng cách chuyển `production` về v1 và lưu `evidence/10-prompt-rollback.png`. Metadata trên `lab-agent-run` ghi `prompt_name`, `prompt_label`, `prompt_version`, `prompt_source`; khi lấy managed prompt thành công thì `prompt_source=langfuse`, còn khi Langfuse lỗi thì app dùng local fallback thay vì giả vờ đã fetch prompt managed.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard có time range **60 phút**, refresh **30 giây** và đúng 6 panel:
  1. **Latency percentiles and TTFT** — `latency_ms`, `ttft_ms`; P50/P95/P99 + TTFT P95; đơn vị `ms`; threshold P95 `<= 3000 ms`.
  2. **Request traffic** — count và rate/minute; đơn vị `requests_per_minute`; threshold `>= 1` request/phút.
  3. **Error rate and retrieval success** — error rate, error breakdown và retrieval/tool success rate; đơn vị `%`; error-rate threshold `<= 2%`; retrieval guardrail tối thiểu `90%`.
  4. **Cost over time** — tổng cost và cost theo phút; đơn vị `USD`; threshold tổng `<= 2.5 USD`.
  5. **Input and output tokens** — tổng input/output tokens; đơn vị `tokens`; threshold `<= 50,000`.
  6. **Quality proxy** — mean `quality_score`; thang `0..1`; threshold `>= 0.75`.
- **SLO và lý do chọn:** Primary SLO là **99.5% request trong cửa sổ 28 ngày đạt `response_sent` với `latency_ms <= 3000`**. Ngưỡng này tập trung vào trải nghiệm người dùng: request phải vừa thành công vừa không chậm quá 3 giây. Ngoài SLO chính, hệ thống có guardrail error rate tối đa 2%, retrieval success tối thiểu 90%, quality trung bình tối thiểu 0.75 và daily cost tối đa 2.5 USD.
- **Cách tính error budget:** Với SLO 99.5%, error budget là `100% - 99.5% = 0.5%`. Ví dụ với 10,000 request trong cửa sổ 28 ngày, số request được phép không đạt SLO là `10,000 × 0.5% = 50` request. Khi error budget bị tiêu thụ nhanh, ưu tiên ổn định hệ thống/rollback thay vì tiếp tục đưa thay đổi mới vào production.
- **Ba alert và runbook tương ứng:** 
  - `HighLatencyP95`: warning khi P95 latency > 3000 ms liên tục 5 phút; Slack `#k4-l3b-alerts`; runbook `docs/alerts.md#alert-1`. Kiểm tra panel latency → lọc request chậm → mở trace và so sánh retrieval/generation; mitigation có thể rollback prompt hoặc khôi phục dependency chậm.
  - `HighRequestErrorRate`: critical khi `request_failed/request_received > 2%` liên tục 5 phút; Slack `#k4-l3b-alerts`; runbook `docs/alerts.md#alert-2`. Kiểm tra error breakdown → correlation ID → trace lỗi; rollback thay đổi gần nhất hoặc khôi phục dependency/fallback.
  - `LowRetrievalSuccessRate`: warning khi retrieval success < 90% liên tục 10 phút; Slack `#k4-l3b-alerts`; runbook `docs/alerts.md#alert-3`. Lọc log `tool_name=retrieval` + `tool_success=false`, mở retrieval span; mitigation bằng fallback context, giảm concurrency khi quá tải hoặc khôi phục vector store.

## 7. Điều tra challenge

> Phần này bắt buộc phải khớp **evidence/12 → evidence/13 → evidence/14**. Tôi không điền giả dữ liệu vì `config/challenge.json` và các evidence runtime không nằm trong REPORT được cung cấp.

- **Challenge ID:** **[CẦN ĐIỀN]**
- **Khoảng thời gian điều tra:** **[CẦN ĐIỀN theo time range ở `evidence/12-incident-metric.png`]**
- **Triệu chứng từ metrics:** **[CẦN ĐIỀN: metric nào spike/drop, baseline bao nhiêu, incident bao nhiêu]**. Ảnh metric phải cho thấy baseline và đoạn bất thường trên **cùng trục thời gian**.
- **Log line và correlation ID liên quan:** **[CẦN ĐIỀN event + `correlation_id=req-........` từ `evidence/13-incident-log.png`]**.
- **Trace ID và span gây ảnh hưởng:** **[CẦN ĐIỀN trace ID + `retrieval` hoặc `generation` từ `evidence/14-incident-trace.png`]**.
- **Root cause:** **[CẦN ĐIỀN theo evidence, không đoán]**.
- **Fix action:** **[CẦN ĐIỀN hành động đã khôi phục hệ thống]**.
- **Preventive measure:** Giữ alert symptom-based tương ứng, runbook Metrics → Logs → Traces, test regression cho scenario liên quan và dùng rollback/fallback khi vượt SLO/guardrail. **[BỔ SUNG chi tiết đúng với incident thực tế]**.

**Khung viết sau khi có evidence:**  
“Metric cho thấy **[latency/error/cost/retrieval success]** bất thường trong **[thời gian]** so với baseline. Log event **[event]** có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng correlation ID cho thấy span **[retrieval/generation]** **[chậm/lỗi/token tăng]**. Vì vậy root cause là **[...]**. Tôi khôi phục bằng **[...]** và phòng ngừa tái diễn bằng **alert/runbook/test/guardrail [...]**.”

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Tôi dùng một `correlation_id` xuyên suốt middleware → structured log → agent → Langfuse metadata. Đây là khóa nối ba lớp observability, giúp từ một điểm bất thường trên metric truy ra đúng request trong log và đúng span trong trace thay vì phải đoán.
- **Một lỗi/blocker đã gặp:** Phần tracing/prompt evidence dễ thiếu metadata hoặc prompt link nếu chỉ tạo root trace mà không cập nhật child observation đúng loại; ngoài ra giao diện Langfuse có thể không hiển thị metadata/prompt version ở vị trí mong đợi nếu code chưa attach các field đó vào observation.
- **Cách tìm nguyên nhân và xử lý:** Tôi kiểm tra cây trace để bảo đảm `lab-agent-run` là parent của `retrieval` và `generation`, sau đó gắn `correlation_id` và prompt metadata vào observation. Generation được ghi model, usage token và cost; prompt được resolve theo name/label và link managed prompt khi Langfuse khả dụng. Tôi đối chiếu lại bằng trace detail và evidence screenshot thay vì chỉ dựa vào code.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics dùng để xác định **hệ thống đang có triệu chứng gì và khi nào**. Logs dùng để chọn **request cụ thể nào bị ảnh hưởng** thông qua `correlation_id`. Trace dùng để xác định **bước nào bên trong request** (retrieval hay generation) là nơi latency/error/token tăng. Root cause chỉ được kết luận sau khi ba lớp evidence này khớp nhau.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt được version hóa để biết chính xác request dùng cấu hình nào và rollback nhanh khi candidate gây regression. Token/cost giúp phát hiện prompt/output phình bất thường. SLO biến yêu cầu vận hành thành ngưỡng đo được; error budget cho biết mức lỗi/chậm hệ thống có thể chấp nhận trước khi cần ưu tiên độ ổn định. Rollback là cơ chế giảm thời gian khôi phục khi thay đổi prompt gây vấn đề.
- **Điều quan trọng nhất đã học:** Observability không chỉ là “có log” mà phải tạo được chuỗi bằng chứng có thể truy vết: **metric → correlation ID trong log → span trong trace → root cause → fix**. Khi các lớp cùng dùng metadata nhất quán, việc điều tra incident trở nên có căn cứ và nhanh hơn.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** REPORT hiện đã hoàn thiện phần mô tả kỹ thuật theo source/config của repo. Trước khi nộp cần thay toàn bộ ô **[CẦN ĐIỀN]** bằng số liệu/ID từ evidence runtime thật: commit SHA cuối, Challenge ID, kết quả validators/pytest, trace count/IDs, P95/TTFT/retrieval success và chuỗi incident metric → log → trace.

## 9. Checklist trước khi nộp

- [ ] Đã thay toàn bộ **[CẦN ĐIỀN]** bằng dữ liệu thật từ commit/evidence cuối.
- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace và dùng cùng request/correlation ID.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân `day13-k4-l3b-02600` và ảnh không lộ key/secret.
- [ ] `day13-chat` có v1/v2, labels baseline/candidate/production và evidence rollback production về version cũ.
- [ ] Dashboard ảnh runtime thể hiện đủ 6 panel; latency có TTFT; errors có retrieval success; time range và threshold nhìn được.
- [ ] Repository chạy lại được theo README và validators/tests đều chạy trên commit nộp.
- [ ] Không có `.env`, secret, API key, PII thô, `config/challenge.json` hoặc evidence của người khác/lớp khác trong Git.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
