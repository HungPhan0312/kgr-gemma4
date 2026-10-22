# kgr-gemma4: Tác nhân mã nguồn cục bộ dẫn đường bằng đồ thị với Gemma 4

Kho lưu trữ chính thức cho bài báo nghiên cứu và quy trình thực nghiệm tham dự cuộc thi **Google - Lộ trình chứng nhận ứng viên Gemma 4 Developer Agent** trên Kaggle[cite: 1, 15, 16].

* **Mô hình mục tiêu:** 'google/gemma-4-E4B-it' ('Gemma 4 - gemma-4 - V1') và 'embeddinggemma-2' (740M)[cite: 10, 11, 12, 16].
* **Phần cứng mục tiêu:** Thiết lập phần cứng người tiêu dùng với một bộ tăng tốc ('GPU T4 x2')[cite: 1, 2, 11, 12].
* **Bộ dữ liệu tiêu chuẩn:** 'princeton-nlp/SWE-bench_Lite' ('split="test"', 'n_issues=40', 'seed=42')[cite: 12].
* **Hạng mục giải thưởng mục tiêu:** Bài báo xuất sắc nhất (15.000 đô la), nguồn tài nguyên mới xuất sắc nhất (10.000 đô la) và ứng dụng mới xuất sắc nhất (10.000 đô la)[cite: 9, 10].

---

## 1. Tổng quan và động lực nghiên cứu

Các công cụ lập trình và hệ thống kỹ thuật phần mềm tiên tiến nhất hiện nay dựa trên các mô hình API khổng lồ chạy trên cơ sở hạ tầng đám mây thương mại kết nối internet, khiến kỹ thuật phần mềm cao cấp nằm ngoài tầm với của nhiều nhà phát triển muốn hoạt động ngoại tuyến trên phần cứng thông thường[cite: 1, 2]. Dù các mô hình cục bộ nhỏ đã có những tiến bộ nhanh chóng, chúng vẫn gặp khó khăn lớn với kỹ thuật phần mềm phức tạp nhiều lượt xử lý, hiện tượng cạn kiệt bộ nhớ RAM, bão hòa bộ nhớ đệm chú ý KV-cache bậc hai và sự đánh đổi giữa việc định vị đúng vùng mã nguồn nhưng tạo bản vá lỗi bị sai trên các cơ sở mã lớn[cite: 2, 10, 12].

Dự án **'kgr-gemma4'** giải quyết các thách thức trên thông qua việc kết hợp 4 thành phần cốt lõi[cite: 15, 16]:
1. **Xây dựng đồ thị kho lưu trữ ('ast' -> 'networkx'):** Phân tích cú pháp các kho mã nguồn Python thành các nút 'File', 'Class', 'Function', 'Test' được kết nối bởi các cạnh 'DEFINES', 'CALLS', 'IMPORTS', 'INHERITS' và 'TESTED_BY'[cite: 12, 16].
2. **Cắt lát cây cú pháp trừu tượng tất định ('DependencyPruner'):** Loại bỏ các nhánh thực thi không liên quan thông qua lớp 'ast.NodeVisitor' ('visit_FunctionDef', 'call_graph', 'func_nodes') trước khi tổng hợp ngữ cảnh[cite: 11, 16].
3. **Truy xuất lai ghép đa kênh:** Kết hợp kênh từ vựng 'BM25', các ký hiệu 'AST', véc-tơ dày đặc từ 'embeddinggemma-2' và điều hướng lân cận trên đồ thị trong ngân sách ngữ cảnh chặt chẽ ('top_k=10' hàm hiển thị cho mô hình, 'context_char_budget=24000' ký tự tương đương khoảng '6k' token ngữ cảnh)[cite: 10, 12, 16].
4. **Suy luận nhiều lượt và kiểm chứng Lặp:** Thực thi chu trình có cấu trúc gồm lập chiến lược ('Strategist') -> điều hướng đồ thị ('Graph Navigation') -> phản biện tái lập kế hoạch ('Critic' với 'critic_rounds=2') -> sinh bản vá ('Patch Generation') -> bộ kiểm chứng đồ thị sửa đổi bản vá ('Graph Verifier' với 'verifier_rounds=2')[cite: 12, 16].

---

## 2. Sơ đồ kiến trúc hệ thống

    [Mô tả lỗi (Issue Description) + Cơ sở mã kho lưu trữ (SWE-bench Lite)]
           │
           ▼
    [1. Bộ xây dựng đồ thị kho lưu trữ (Python ast -> networkx + DependencyPruner)]
      ├── Các nút (Nodes): File, Class, Function, Test
      └── Các cạnh (Edges): DEFINES, CALLS, IMPORTS, INHERITS, TESTED_BY
           │
           ▼
    [2. Bộ truy xuất ngữ cảnh lai ghép (Hybrid Context Retriever)]
      ├── Từ vựng (BM25 + Ký hiệu AST) + Nhúng dày đặc (embeddinggemma-2) + Bước nhảy đồ thị
      └── Ngân sách ngữ cảnh: top_k=10 hàm, context_char_budget=24000 (~6k token)
           │
           ▼
    [3. Tác nhân SWE Gemma 4 cục bộ (google/gemma-4-E4B-it)]
      ├── Lập chiến lược và điều hướng đồ thị (Strategist and Graph Navigation)
      ├── Phản biện tái lập kế hoạch (Critic Re-planning, critic_rounds=2)
      └── Kiểm chứng đồ thị và sửa bản vá (Graph Verifier, verifier_rounds=2, temperature=0.0)
           │
           ▼
    [4. Đánh giá & xuất kết quả (Evaluation & Export)]
      ├── Khung đối chứng 7 nhánh (A1-A7): Recall@k, MRR, Groundedness, Lỗi Loại I/II/III
      └── Xuất định dạng chuẩn SWE-bench (predictions.jsonl)

---

## 3. Bảy cấu hình kiến trúc đối chứng (A1–A7)

Khung đánh giá thực nghiệm trong tệp 'codekgr.py' tiến hành đo lường và đối sánh bảy cấu hình kiến trúc được ký hiệu từ 'A1' đến 'A7'[cite: 12, 13, 15, 16]:
* **'A1':** Truy xuất cơ sở chỉ sử dụng kênh từ vựng 'BM25'[cite: 12, 13].
* **'A2':** Truy xuất và điều hướng cấu trúc chỉ sử dụng đồ thị ('graph-only')[cite: 12, 13].
* **'A3':** Truy xuất lai ghép 'Code-KGR hybrid' kết hợp giữa từ vựng và đồ thị[cite: 12, 13].
* **'A4':** Truy xuất lai ghép kết hợp bộ cắt lát cây cú pháp tất định 'DependencyPruner'[cite: 11, 12, 13, 16].
* **'A5':** Cấu hình 'A4' bổ sung vòng lặp lập chiến lược và phản biện tái lập kế hoạch ('Strategist/Critic' với 'critic_rounds=2')[cite: 12, 13, 16].
* **'A6':** Cấu hình 'A5' bổ sung vòng lặp bộ kiểm chứng đồ thị sửa đổi bản vá ('Graph Verifier' với 'verifier_rounds=2')[cite: 12, 13, 16].
* **'A7':** Kiến trúc 'gemma-4-codekgr' hoàn chỉnh tích hợp suy luận dẫn đường bằng đồ thị, cắt lát phụ thuộc và kiểm chứng đồ thị lặp trên mô hình 'Gemma 4'[cite: 12, 13, 16].

---

## 4. Cấu trúc kho lưu trữ và hướng dẫn sử dụng

* **'codekgr.py':** Tệp mã nguồn chính bằng ngôn ngữ 'Python' chứa thiết lập cấu hình 'CFG' ('seed=42', 'n_issues=40', 'time_budget_hours=9.5', 'max_new_tokens=1024', 'temperature=0.0'), cơ sở mã giả lập 'MOCK_CODEBASE' kèm kiểm thử 'UNIT_TEST_CODE', lớp cắt lát 'DependencyPruner', bộ dựng đồ thị 'networkx', khung đánh giá 'A1'–'A7' (tính toán 'Recall@k', 'MRR', 'groundedness', phân loại lỗi Loại I/II/III, 'bootstrap CIs', chỉ số đại diện định vị đúng 'location-correct proxy') và bộ xuất tệp 'predictions.jsonl'[cite: 11, 12, 15, 16].
* **'README.md':** Tài liệu mô tả kiến trúc hệ thống và hướng dẫn thực nghiệm của dự án[cite: 15, 16].

### Cách chạy chương trình thực nghiệm

1. Cài đặt các thư viện phụ thuộc ('datasets', 'networkx', 'numpy', 'pandas')[cite: 12]:
   'pip install datasets networkx numpy pandas'
2. Thực thi tệp mã nguồn chính của dự án[cite: 12, 15, 16]:
   'python codekgr.py'
3. Tệp dự đoán bản vá đầu ra chuẩn định dạng 'SWE-bench' sẽ được lưu tại đường dẫn '/kaggle/working/codekgr/predictions.jsonl' (hoặc './codekgr_work/predictions.jsonl' khi chạy cục bộ) để chấm tỷ lệ giải quyết trên máy có cài đặt Docker[cite: 12, 16].
