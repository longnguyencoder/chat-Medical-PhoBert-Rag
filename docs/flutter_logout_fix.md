# Hướng Dẫn Sửa Lỗi Đăng Xuất (Navigator Error)

Bạn đang gặp lỗi: `Navigator.onGenerateRoute was null, but the route named "/login" was referenced`.

Lỗi này xảy ra do ứng dụng Flutter chưa định nghĩa route tên là `'/login'` trong `MaterialApp`, nhưng chức năng đăng xuất lại cố gắng điều hướng đến nó.

## Cách Sửa

### 1. Khai báo route `/login` trong `main.dart`

Mở file `main.dart` của bạn, tìm widget `MaterialApp` và đảm bảo bạn đã khai báo `routes`:

```dart
// main.dart

MaterialApp(
  // ... các cấu hình khác
  initialRoute: '/', // Hoặc trang bắt đầu của bạn
  routes: {
    '/': (context) => HomeScreen(), // Ví dụ
    '/login': (context) => LoginScreen(), // <--- BẮT BUỘC PHẢI CÓ DÒNG NÀY
    '/home': (context) => HomeScreen(),
    // ... các route khác
  },
);
```

### 2. Sửa hàm Đăng Xuất (Logout)

Trong hàm xử lý đăng xuất (thường ở `SettingScreen` hoặc `ProfileScreen`), hãy đảm bảo bạn dùng lệnh điều hướng đúng để xóa hết lịch sử stack và về trang login:

```dart
Future<void> _handleLogout(BuildContext context) async {
  // 1. Xóa token/user data (Ví dụ dùng SharedPreferences)
  // final prefs = await SharedPreferences.getInstance();
  // await prefs.clear();

  // 2. Điều hướng về trang Login và xóa hết các màn hình trước đó
  Navigator.of(context).pushNamedAndRemoveUntil(
    '/login', 
    (Route<dynamic> route) => false // Xóa tất cả các route trong stack
  );
}
```

### 3. Kiểm tra lại tên Route

Đảm bảo `LoginScreen` của bạn không định nghĩa tên route khác (ví dụ `LoginScreen.routeName` có thể là `'/auth/login'` thay vì `'/login'`). Hãy thống nhất một cái tên duy nhất.
