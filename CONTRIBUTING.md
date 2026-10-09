# 协作与版本管理约定

本仓库采用 **GitHub Flow**：`main` 永远是可直接发布的可用版本，
所有改动都通过短命的特性分支 + Pull Request 进入 `main`。

## 一、日常开发循环

```bash
# 1. 每次动手前同步主干
git switch main && git pull

# 2. 按改动类型开一个分支
git switch -c feat/add-shopping-list

# 3. 完成一小块逻辑就提交一次
git add index.html
git commit -m "feat(plan): 新增一周购物清单区块"

# 4. 推上去，在网页上开 Pull Request
git push -u origin feat/add-shopping-list

# 5. 在页面点 Squash and merge 合并
# 6. 回到本地清理分支
git switch main && git pull && git branch -d feat/add-shopping-list
```

### 分支命名

格式为 `类型/简短描述`，全部小写、用连字符分词：

| 前缀 | 用途 | 例子 |
|---|---|---|
| `feat/` | 新增内容或功能 | `feat/add-shopping-list` |
| `fix/` | 修错误 | `fix/week2-calorie-typo` |
| `docs/` | 只改说明文档 | `docs/update-readme` |
| `refactor/` | 重构，不改呈现效果 | `refactor/extract-color-vars` |
| `style/` | 改配色、排版、视觉 | `style/soften-day-header` |
| `chore/` | 杂务、依赖、配置 | `chore/bump-actions-version` |

## 二、提交信息规范（Conventional Commits）

格式：

```
类型(可选范围): 描述
```

描述用中文或英文都行，但同一个仓库保持一致；**动词开头、说明做了什么**。

| 类型 | 含义 | 对版本号的影响 |
|---|---|---|
| `feat` | 新增功能 | MINOR +1 |
| `fix` | 修复缺陷 | PATCH +1 |
| `docs` | 只改文档 | 无 |
| `refactor` | 重构，外部行为不变 | 无 |
| `style` | 格式、配色、排版 | 无 |
| `perf` | 性能优化 | PATCH +1 |
| `test` | 测试相关 | 无 |
| `build` | 构建、依赖 | 无 |
| `ci` | CI 配置 | 无 |
| `chore` | 其他杂务 | 无 |
| `revert` | 回滚某次提交 | 视情况 |
| `BREAKING CHANGE` | 不兼容变更 | MAJOR +1 |

反例（不要这样写）：

```
更新一下
fix bug
改了改样式
```

正例：

```
feat(plan): 增加周五碳水循环的可选项
fix(day3): 修正周三晚餐蛋白质克数
style(theme): 降低表头底色饱和度
docs(readme): 补充部署方式说明
```

## 三、版本发布

采用语义化版本 `MAJOR.MINOR.PATCH`：

- **MAJOR** —— 有不兼容的改动（比如内容结构彻底重做）
- **MINOR** —— 新增内容或功能，向后兼容
- **PATCH** —— 修复错误

打标签并发布：

```bash
git switch main && git pull
git tag -a v1.1.0 -m "新增购物清单与备餐建议"
git push origin v1.1.0
```

推送后到 GitHub 的 **Releases** 页面点 **Draft a new release**，
选择刚推的标签，写清本次变更要点，即为一个正式发布点。

## 四、自动化检查

`.github/workflows/validate.yml` 会在每次 push 到 `main` 和每个 Pull Request 上自动运行：

1. **页面结构校验**（`scripts/check_html.py`）—— 检查标签配平、id 唯一性、
   页内锚点是否都有落点、本地资源引用是否存在、必要元信息是否齐全。
2. **提交信息校验** —— 在 PR 上检查每个提交是否符合上面的格式约定。

本地想先跑一遍再推：

```bash
python3 scripts/check_html.py index.html
```

## 五、禁止事项

- 不要直接往 `main` 推提交（分支保护已开启），一律走 Pull Request。
- 不要把 `index.html` 拆成多个文件再引外部资源 —— 这个项目**刻意保持自包含**，
  单个 HTML 文件即可离线打开、可直接拖到任意静态托管。
- 不要提交 `.DS_Store`、编辑器配置、本地压缩包（`.gitignore` 已覆盖）。
