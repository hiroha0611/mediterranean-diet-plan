# 地中海饮食 · 增肌减脂周计划

[![页面校验](https://github.com/hiroha0611/mediterranean-diet-plan/actions/workflows/validate.yml/badge.svg)](https://github.com/hiroha0611/mediterranean-diet-plan/actions/workflows/validate.yml)

一份中文的地中海饮食周历，面向**增肌减脂**目标，按天给出餐食安排、训练内容与时间轴，并附注意事项与执行提示。

## 内容包含

- 每日餐食与进食时间轴
- 训练日安排（力量 / 有氧 / 休息）与组次说明
- 每日热量参考
- 窗口期说明、注意事项与执行 tips

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `index.html` | 整个网站。单文件、自包含、零外部依赖，双击即可在浏览器打开 |
| `CONTRIBUTING.md` | 分支命名、提交信息规范、版本发布约定 |
| `scripts/check_html.py` | 页面结构校验脚本，仅依赖 Python 标准库 |
| `.github/workflows/validate.yml` | 自动化校验工作流 |

## 使用方式

**本地查看**：直接双击 `index.html`。

**上线部署**：把 `index.html` 放到任意静态托管即可，例如 Cloudflare Pages、GitHub Pages、或各家对象存储。

## 技术说明

页面是单个自包含的 HTML 文件：样式全部内联在 `<style>` 中，不含外部图片、字体、脚本或任何网络请求。因此它可以离线使用，也能随意迁移，不需要构建步骤。

内置响应式断点（940px / 760px），手机上也能正常阅读。

## 校验

改完页面后，推之前先本地跑一遍：

```bash
python3 scripts/check_html.py index.html
```

它会检查：

| 检查项 | 说明 |
| --- | --- |
| 标签结构配平 | 正确处理 void 元素与 HTML5 可选结束标签 |
| id 唯一性 | 重复 id 会让页内锚点跳错位置 |
| 页内锚点完整 | 每个 `#xxx` 都要能找到落点 |
| 本地资源存在 | 相对路径引用的文件必须真实存在 |
| 必要元信息 | DOCTYPE / charset / viewport / title / html lang |

同一个脚本也会在 GitHub Actions 里自动跑，每次 push 到 `main` 或提交 PR 都会执行。

## 版本管理

本仓库采用 **GitHub Flow**：`main` 永远是可发布的可用版本，所有改动都通过短命的特性分支加 Pull Request 进入。

完整约定见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。要点：

- 分支名用 `类型/简短描述`，例如 `feat/add-shopping-list`
- 提交信息用 `类型(可选范围): 描述`，例如 `fix(day3): 修正周三晚餐蛋白质克数`
- `main` 已开启分支保护：禁止直接推送，必须走 Pull Request 且通过 `html-check`
- 发布时打语义化版本标签并建 Release

查看历史版本：<https://github.com/hiroha0611/mediterranean-diet-plan/releases>
