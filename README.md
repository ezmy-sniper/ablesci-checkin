# 科研通每日签到（Windows）

使用 Python + Playwright 打开科研通并点击签到，每天由 Windows 任务计划运行。首次手动登录，不需要把密码写进代码。官网签到说明：https://www.ablesci.com/knowledge/detail?id=21 。

## 上传 GitHub

解压源码包，在 GitHub 新建仓库，将解压文件夹中的源码文件上传到仓库根目录（包含 `.gitignore`）。README.md 会自动显示为项目说明。不要只上传 ZIP 文件，否则仓库不能直接浏览源码。

源码包仅包含程序、默认配置、安装脚本和说明；每位使用者都需要在自己的电脑上安装依赖并登录。`session.json`、`.venv/`、`logs/` 不属于源码，已加入 `.gitignore`。如果通过网页上传文件，也只选择源码包中的文件。

每日运行由本机 Windows 任务计划负责，上传 GitHub 不会自动启动签到。本项目未配置 GitHub Actions。

## 使用

安装 Python 3.10 或更新版本，将整个文件夹放在固定位置，在该文件夹中打开 PowerShell，依次执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe checkin.py login
.\.venv\Scripts\python.exe checkin.py run --headed
powershell -ExecutionPolicy Bypass -File .\install-task.ps1 -At '09:00'
```

第二步在打开的浏览器中登录，完成验证码后回终端按回车。第三步应确认签到成功后再安装任务。每天 09:00 按 Windows 本机时区运行；电脑需开机、当前用户需登录。错过时间可在系统恢复可运行时补跑，关机期间无法保证每天签到。再次运行 install-task.ps1 可修改时间。计划使用独立 Python 环境，不依赖 Codex 打开。

## 网站适配与验证范围

2026-09-22 已通过登录后的页面验证：按钮文字为“今日打卡签到”，默认使用 `.fly-signin button.btn-sign` 定位。点击后检查网站签到请求是否返回成功；再次运行时根据个人签到区判断今日已签到。已实际确认积分增加及连续签到天数更新。不会把首页其他人的签到动态当成当前账号签到成功。

若按钮在其他页面，将 config.json 的 url 改为该科研通页面；若默认识别不到，在浏览器开发者工具中找到实际签到按钮，填写 button_selector 的 CSS 选择器。signed_selector 可填写仅在当前用户已签到时出现的元素选择器，不能填始终存在的容器。不要直接照抄未验证的选择器。点击后只有检测到已签到按钮或网站成功提示才返回成功，否则返回非零退出码。

日志：logs/checkin.log。登录过期或验证码出现时，重新执行 login；程序不处理验证码。session.json 保存能访问账号的登录凭据，请勿分享或上传。若登录后依然不能保留会话，需要根据网站当前登录机制进一步适配。

删除每日任务：

```powershell
Unregister-ScheduledTask -TaskName 'AbleSci-Daily-Checkin' -Confirm:$false
```

任务计划程序中的上次运行结果 0 表示已明确确认签到或今日已签到；1 表示失败，请查看日志。程序不自动重试提交，避免结果不明时重复点击。
