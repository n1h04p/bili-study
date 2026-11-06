# B站学习助手（本地适配版）

在本机运行的独立 MCP 插件，参考 dsh-bili-subagent 的扫码登录流程，适配 Codex。

支持：单独扫码登录、检查账号、读取最近的 @我的、视频详情和分P、按时间段分页读取字幕、热门评论、搜索，以及按授权发布视频评论、纯文字动态、点赞和收藏视频。
ChatGPT 嵌入视频窗口：通过 `bili_show_video_window` 显示最近 @ 我的视频封面卡片，选中后尝试在窗口中加载 B站官方播放器，并提供 B站原页链接。此列表不是 B站观看历史；内嵌播放是否可用取决于 ChatGPT 客户端和 B站播放器的嵌入策略。
字幕读取不等于观看视频画面；没有字幕时会明确返回，不会用简介冒充视频内容。
0.2.0 新增指定时间点提取画面，返回可直接查看的图片。结合字幕定位代码、电路图和操作步骤；少量抽帧不等于观看完整视频。
此版本没有连续视频播放、本地语音转写、自动巡检、私信、点赞、收藏或投币能力。

## 账号与数据

- 使用手机 B站扫描插件生成的二维码并自行确认，使用你指定的另一个账号。
- 不读取 DSH 或浏览器的账号凭证。
- 新凭证保存于当前用户 `%LOCALAPPDATA%\BiliStudy\credential.dpapi`，由 Windows DPAPI 加密。
- 二维码、字幕缓存与画面截图也在该目录。没有网络监听端口、遥测或第三方登录服务。
- 登录和其他请求只连接 B站；字幕下载只允许 B站/hdslb 的 HTTPS 域名，不跟随重定向，也不携带登录 Cookie。
- 画面提取只读取 B站接口返回的 bilivideo.com / bilivideo.cn HTTPS 视频源，不跟随重定向、不携带账号 Cookie。按 HTTP Range 获取所需片段，单次最多64MiB，使用 PyAV 本地解码，不下载整部视频。不支持受 DRM 保护的视频。
- 遇到网络错误、风控或验证时返回错误，不自动规避限制。
- 本项目采用社区 API 库，不能保证网站接口长期不变。

## 使用

插件安装后重新加载聊天，使 `bili-study` 工具生效。然后要求扫码登录、读取“@我的”或提供视频 BV 号。
使用 `bili_video_info` 查分P；`bili_subtitles` 的 page 从 1 开始，start/end 以秒计。
按 `next_offset` 继续同一时间范围，直到为 null 才是读完。完整字幕缓存于本机，不必重新下载整段视频。
使用 `bili_video_frame(bvid, seconds, page)` 取指定时间点画面，page从1开始，seconds是该分P内的秒数。返回图片、实际时间戳和分P信息。
使用 `bili_video_gallery(limit)` 获取卡片数据；`bili_show_video_window(limit)` 在支持 MCP Apps 的 ChatGPT 客户端中打开嵌入窗口。现有读取与发布工具没有附带界面，避免频繁重绘。
使用 `bili_post_comment(bvid, text)` 在指定视频下发布顶层评论；`bili_post_dynamic(text)` 发布纯文字动态。两者都要求已登录和用户明确授权发布具体文字，不自动重试。发布失败时先检查 B站页面，避免重复发送。
使用 `bili_reply_comment(bvid, root_id, text)` 回复视频中指定编号的评论。回复前核对视频和评论编号，不自动重试。
使用 `bili_like_video(bvid)` 点赞，`bili_favorite_video(bvid, media_id)` 收藏。收藏默认进入账号的第一个视频收藏夹；可指定 `media_id`。已点赞或已在目标收藏夹中的视频不会重复操作。用户已授权在当前观看任务中对认真看过且认为好看的视频自行点赞、收藏；仅凭标题或少量画面不作此判断。插件不在后台自动巡视频。

独立登录可双击根目录 `扫码登录.cmd`；程序返回唯一二维码图片路径，180秒内扫码。
本地检查：`.venv\Scripts\python.exe plugin\server.py --call whoami`。
开发测试：`.venv\Scripts\python.exe -m unittest discover -s tests -v`；MCP 握手：`.venv\Scripts\python.exe tests\mcp_smoke.py`。

本机路径固定为 `D:\chatGPT\bili-study`。插件连接该目录中的源码和独立运行环境，请保留目录。
卸载插件：Codex CLI 的 `plugin remove bili-study@bili-study-local`；不会删除账号缓存。

## 来源

参考仓库：https://github.com/Yuuyuko-uu/dsh-bili-subagent
固定快照：efae852a276b7b120ca9d8ef6cd5080da3023005。
保留上游 MIT 授权，详见 plugin/THIRD_PARTY_NOTICES.md 与 plugin/licenses/。
