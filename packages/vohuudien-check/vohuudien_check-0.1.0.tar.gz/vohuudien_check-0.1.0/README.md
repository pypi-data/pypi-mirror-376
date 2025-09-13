# vohuudien-check

Một thư viện Python đơn giản giúp:
- Chuẩn hoá tên người dùng (bỏ dấu, khoảng trắng, ký tự đặc biệt)
- Kiểm tra xem tên người dùng có khớp với một tên cụ thể hay không

## 🚀 Cài đặt

```bash
pip install vohuudien-check
```

## 🛠 Sử dụng

```python
import vohuudien_check

# Chuẩn hoá tên người dùng
print(vohuudien_check.normalize_username("Võ Hữu Điền"))
# Kết quả: "vohuudien"

# Kiểm tra tên cụ thể
print(vohuudien_check.is_specific_user("Võ Hữu Điền"))
# Kết quả: True

# Kiểm tra tên không hợp lệ
print(vohuudien_check.is_valid_username("abc@123"))
# Kết quả: False
```

## 📦 Tính năng

- Hỗ trợ chuẩn hoá ký tự tiếng Việt về không dấu
- So sánh tên người dùng không phân biệt hoa/thường
- Kiểm tra định dạng tên có hợp lệ

## 🧑‍💻 Tác giả

**Võ Hữu Điền**  
Giấy phép: MIT
