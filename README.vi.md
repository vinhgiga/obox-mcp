[![Cover Image](assets/cover.png)](https://youtu.be/j_Gsx_FNj0o)

Nhấn vào ảnh để xem video hướng dẫn.

# 🚀 Obox MCP: Thiết lập & Tích hợp Dự án

[English](README.md) | Tiếng Việt

Hướng dẫn này giải thích cách cài đặt và tích hợp Obox MCP vào môi trường lập trình của bạn.

**Obox MCP** là bộ công cụ phát triển toàn diện được thiết kế để tăng cường sức mạnh cho IDE của bạn. Nó cung cấp:
- **Tự động hóa Dự án**: Quản lý dependencies và chạy nhiệm vụ với `just`.
- **Công cụ Ngôn ngữ**: Quản lý môi trường Node.js, Python, và .NET.
- **Hệ thống Tệp**: Tìm kiếm và điều hướng tệp nâng cao với `fd` và `ripgrep`.
- **Tiện ích Hệ thống**: Trình cài đặt đa nền tảng và tích hợp shell.

---

## 🆚 Tại sao lại là Obox MCP?

### ❌ Không có Obox MCP
LLMs là môi trường thực thi biệt lập. Chúng không thể nhìn thấy hệ thống của bạn hoặc chạy mã. Bạn sẽ gặp:

- ❌ **Thực thi Thủ công**: AI gợi ý mã lệnh, nhưng *bạn* phải chuyển sang terminal để chạy chúng.
- ❌ **Đoán Mò**: AI ảo giác về đường dẫn tệp hoặc cấu trúc dự án mà nó không thể nhìn thấy.
- ❌ **Ngữ cảnh Lỗi thời**: Bạn phải sao chép-dán nội dung tệp thủ công để AI hiểu dự án của bạn.

### ✅ Có Obox MCP
Obox MCP cung cấp cho tác nhân AI của bạn **tay** và **mắt**. Nó có thể tự động chạy lệnh, quản lý tệp và điều hướng dự án của bạn mà bạn không cần động tay.

**Thêm `use obox` vào prompt của bạn:**

> "Tìm tất cả các tệp Python có chứa 'TODO' và liệt kê vị trí của chúng."

> "Khởi tạo dự án FastAPI mới, cài đặt dependencies, và chạy server."

Obox MCP lấy thông tin dự án theo thời gian thực, thực hiện các tác vụ build phức tạp và quản lý môi trường của bạn trực tiếp. Không cần chuyển tab, không cần sao chép-dán thủ công, chỉ có kết quả.

---

## 🛠 Yêu cầu Tiên quyết

Obox MCP được tối ưu hóa để chạy bằng **Astral `uv`**. Đảm bảo bạn đã cài đặt `uv` trên hệ thống của mình:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -c "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 🔌 Cấu hình Client

<details>
<summary><strong>Cursor</strong></summary>

[Tài liệu Cursor MCP](https://docs.cursor.com/context/model-context-protocol)

### Cấu hình Cursor

1. Đi tới: **Settings** -> **Cursor Settings** -> **General** -> **MCP** -> **Add new global MCP server**.
2. Dán cấu hình sau vào tệp `~/.cursor/mcp.json` của Cursor.

```json
{
  "mcpServers": {
    "obox": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/obox",
        "/absolute/path/to/obox/main.py"
      ]
    }
  }
}
```

</details>

<details>
<summary><strong>VS Code GitHub Copilot</strong></summary>

[Tài liệu VS Code MCP](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)

### Cấu hình VS Code

1. Mở Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
2. Gõ: `MCP: Open User Configuration`.
3. Dán nội dung vào tệp.

```json
{
  "servers": {
    "obox": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/obox",
        "/absolute/path/to/obox/main.py"
      ]
    }
  }
}
```


</details>

<details>
<summary><strong>Claude Code</strong></summary>

[Tài liệu Claude Code MCP](https://docs.anthropic.com/en/docs/claude-code/mcp)

### Lệnh CLI

Chạy lệnh sau trong terminal của bạn để thêm MCP server:

```bash
claude mcp add obox -- uv run --project /absolute/path/to/obox /absolute/path/to/obox/main.py
```

### Cấu hình Thủ công (Claude Desktop)

Thêm nội dung này vào `claude_desktop_config.json` của bạn:

```json
{
  "mcpServers": {
    "obox": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/obox",
        "/absolute/path/to/obox/main.py"
      ]
    }
  }
}
```

</details>

<details>
<summary><strong>Google Antigravity</strong></summary>

[Tài liệu Antigravity MCP](https://antigravity.google/docs/mcp)

### Cấu hình Antigravity

1. Mở Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
2. Gõ: `Antigravity: Manage MCP Servers`.
3. Nhấp **View Raw Config**.
4. Dán nội dung vào tệp.

```json
{
  "mcpServers": {
    "obox": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/obox",
        "/absolute/path/to/obox/main.py"
      ]
    }
  }
}
```

</details>

---

## 💡 Mẹo Quan Trọng

### Thêm Quy Tắc (Rule)

Để tránh phải gõ `use obox` trong mỗi prompt, hãy thêm một quy tắc vào MCP client của bạn để tự động gọi các công cụ Obox cho các tác vụ phát triển.

**Khuyến nghị:** Sao chép nội dung của [.github/copilot-instructions.md](.github/copilot-instructions.md) vào:

- **Cursor**: `Cursor Settings` > `Rules`
- **Claude Code**: `CLAUDE.md`
- **Các Client Khác**: System prompt tương đương hoặc cài đặt quy tắc.
