# Login Error Codes

## Mã lỗi đăng nhập

| Error Code | Message | Mô tả |
|------------|---------|-------|
| `EMAIL_REQUIRED` | Email is required. | Email không được để trống |
| `PASSWORD_REQUIRED` | Password is required. | Password không được để trống |
| `USER_NOT_FOUND` | User not found. Please check your email. | Không tìm thấy user với email này |
| `ACCOUNT_DEACTIVATED` | Account has been deactivated. Please contact support. | Tài khoản đã bị vô hiệu hóa |
| `INVALID_PASSWORD` | Invalid password. | Mật khẩu không đúng |
| `HWID_MISMATCH` | Hardware ID không khớp. Vui lòng đăng nhập từ thiết bị đã đăng ký. | HWID không khớp với thiết bị đã đăng ký |
| `INTERNAL_ERROR` | Internal server error. Please try again later. | Lỗi server nội bộ |

## Cách sử dụng

Khi gọi API `/login`, nếu `success: false`, client có thể kiểm tra `error_code` để xử lý cụ thể:

```javascript
const response = await fetch('/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password, hwid })
});

const result = await response.json();

if (!result.success) {
  switch (result.error_code) {
    case 'USER_NOT_FOUND':
      // Hiển thị thông báo user không tồn tại
      break;
    case 'INVALID_PASSWORD':
      // Hiển thị thông báo mật khẩu sai
      break;
    case 'HWID_MISMATCH':
      // Hiển thị thông báo thiết bị không được phép
      break;
    // ... các case khác
  }
}
```

## Logic HWID

1. **Lần đăng nhập đầu tiên**: Nếu user chưa có HWID trong database, hệ thống sẽ lưu HWID từ request
2. **Lần đăng nhập tiếp theo**: Nếu HWID trong request khác với HWID đã lưu, trả về lỗi `HWID_MISMATCH`
3. **Không có HWID trong request**: Cho phép đăng nhập bình thường (không kiểm tra HWID)