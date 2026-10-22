# Microservices Lab — VS Code + Docker Desktop + PowerShell

Bộ source trích từ tài liệu lab được cung cấp: FastAPI cho User, Product và Order; PostgreSQL riêng cho từng service; Nginx API Gateway; Docker Compose; giao tiếp nội bộ REST.

## Bắt đầu

1. Mở Docker Desktop và chờ Docker Engine ở trạng thái Running.
2. Mở thư mục `microservices-lab` bằng VS Code.
3. Mở Terminal → PowerShell trong VS Code, chạy:

```powershell
docker --version
docker compose version
docker compose config
docker compose up -d --build
docker compose ps
```

4. Mở `http://localhost:8080/health` để kiểm tra gateway.
5. Chạy kiểm thử tự động (PowerShell):

```powershell
./test-lab.ps1
```

6. Có thể xem log bằng `docker compose logs -f` (Ctrl+C để thoát theo dõi log, không dừng container).

## API

- GET `http://localhost:8080/health`
- GET, POST `http://localhost:8080/api/users`
- GET `http://localhost:8080/api/users/{id}`
- GET, POST `http://localhost:8080/api/products`
- GET `http://localhost:8080/api/products/{id}`
- PUT `http://localhost:8080/api/products/{id}/stock?quantity=-2`
- GET, POST `http://localhost:8080/api/orders`
- GET `http://localhost:8080/api/orders/{id}`

## Kiểm tra các PostgreSQL độc lập

```powershell
docker compose exec user-db psql -U postgres -d userdb -c "SELECT * FROM users;"
docker compose exec product-db psql -U postgres -d productdb -c "SELECT * FROM products;"
docker compose exec order-db psql -U postgres -d orderdb -c "SELECT * FROM orders;"
docker compose exec order-db psql -U postgres -d orderdb -c "SELECT * FROM order_items;"
```

## Dừng và xóa tài nguyên

```powershell
docker compose stop              # Tạm dừng, giữ dữ liệu
docker compose start             # Khởi động lại
docker compose down              # Xóa containers/network, vẫn giữ volumes
docker compose down -v           # Xóa cả volumes, MẤT dữ liệu database
```

## Khác biệt nhỏ so với văn bản gốc

- Chỉnh 2 chuỗi URL trong Order Service: văn bản dán có `&quot;` làm Python không hợp lệ.
- Bỏ dòng `version: '3.8'` vì Docker Compose hiện tại không cần và có thể báo obsolete warning.
- Thêm `test-lab.ps1` để dùng đúng cú pháp PowerShell, thay các lệnh `curl`, `grep`, `$()` kiểu Bash trong tài liệu.
- Không thay đổi luồng xử lý nghiệp vụ vốn có trong lab.

## Giới hạn của mã lab

- Mật khẩu database trong Compose chỉ phù hợp môi trường lab cục bộ; không dùng khi triển khai production.
- Nghiệp vụ tạo order trừ tồn kho ở Product Service trước khi lưu Order DB; nếu lưu order thất bại, thiếu cơ chế rollback xuyên service. Chưa sửa để giữ bài gốc.
- Không có khóa/transaction xuyên dịch vụ để bảo vệ tồn kho khi có nhiều đơn đồng thời.
- Các FastAPI service dùng API startup đời cũ có thể có cảnh báo deprecation.
- Tạo container `depends_on` không đảm bảo DB đã sẵn sàng, dù service đã có cơ chế retry kết nối.
