# B站学习助手 · Bili Study

给 Codex 桌面端使用的本地 B站插件。独立扫码登录，读取教学视频字幕，并按时间点提取画面，辅助理解代码、电路图和操作步骤。

社区项目，与 Bilibili、OpenAI 无隶属关系。Windows 10/11，建议 Python 3.12；需要 Codex 桌面端及网络连接。

## 安装

1. 下载本仓库 ZIP，完整解压到长期保留的目录。
2. 双击 `安装插件.cmd`。安装器会自动查找 Python（支持 Codex 自带运行环境），创建独立环境，从 PyPI 官方源安装固定版本依赖，并注册本地插件。
3. 重新加载聊天，要求助手“用 B站学习助手生成登录二维码”。
4. 用你希望授权的 B站账号扫码并在手机确认。每个人使用自己的账号，不需要导入他人 Cookie。

也可用 PowerShell 运行 `Install.ps1 -Python '你的python.exe完整路径'`。
安装后请保留目录；插件运行时会引用其中的文件。更新源码后重新运行安装器。

## 能做什么

- `bili_login_start` / `bili_login_poll`：生成二维码与完成扫码登录。
- `bili_whoami`：检查当前插件账号。
- `bili_mentions`：读取最近的“@我的”。
- `bili_search` / `bili_video_info` / `bili_comments`：搜索、视频详情、分P、热门评论。
- `bili_subtitles`：按分P、时间范围分页读取带时间戳的字幕。
- `bili_video_frame`：按分P和秒数提取一帧，直接作为图片返回给助手。

示例：“读取 BV1Mb411e7re 第11P，18分20秒的画面，解释数码管电路。”
字幕工具 page 从1开始，start/end 为秒；按 next_offset 继续同一范围，直到为 null 才读完。
画面工具 seconds 为该分P内的秒数，返回请求时间、实际时间和截图。

## 能力边界与数据

抽帧配合字幕使用，不是连续观看整段视频。无字幕时会返回明确状态；画面清晰度受原视频影响。仅支持账号正常获准访问、接口可提供普通 DASH 视频流的视频，不支持 DRM 视频。网站接口、网络和风控可能导致请求失败。

凭证使用 Windows DPAPI 加密，仅保存在当前用户 `%LOCALAPPDATA%\BiliStudy\credential.dpapi`。二维码、字幕缓存和截图也位于该目录。插件不读取其他程序的登录凭证，不包含发评论、私信、点赞、收藏、投币、投稿或自动刷站功能。

视频采用 HTTPS Range 按需读取，单次最多64MiB，最高选择1080p。仅允许 B站视频 CDN，不跟随重定向，向 CDN 请求不携带账号 Cookie。无遥测和常驻网络服务。

卸载：`codex plugin remove bili-study@bili-study-local`。账号缓存不会随插件卸载自动删除，可自行删除上述 BiliStudy 数据目录。

## 测试与来源

安装依赖后运行：

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tests\mcp_smoke.py
```

14项测试覆盖凭证加密、登录响应脱敏、字幕分段、视频域名限制、Range流量限制、合成视频定位解码和图片返回。已在 Windows 实测读取 B站课程详情、账号消息、字幕和指定时间画面。尚未完成多台全新电脑上的安装验证。

登录流程和消息字段参考 [Yuuyuko-uu/dsh-bili-subagent](https://github.com/Yuuyuko-uu/dsh-bili-subagent)，固定快照 `efae852a276b7b120ca9d8ef6cd5080da3023005`，保留原 MIT 授权。视频解码使用 PyAV，B站接口使用 bilibili-api-python。详见 `plugin/THIRD_PARTY_NOTICES.md` 和 `plugin/licenses/`。
