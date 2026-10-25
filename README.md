# 小绿鲸论文译文审核 · xiaolujing-review

用于 Codex 的论文二次校译技能：提供英文原文和小绿鲸生成的中文 PDF，由助手对照审核，再将已确认的错误原位修正。

**保留原格式优先**：保持原分页、双栏、字体字号、公式及图表布局。无法安全放回原位置的修改记录为待处理，不自动换字体、缩字或重新排版。

本项目为独立工作流，与小绿鲸官方无隶属关系。

## 下载与安装

### 直接下载

[下载 ZIP](https://github.com/yuhh2026/xiaolujing-review/archive/refs/heads/main.zip)，解压后将文件夹命名为 `xiaolujing-review`，放入个人技能目录：

- Windows：`%USERPROFILE%\.codex\skills\xiaolujing-review`
- macOS / Linux：`~/.codex/skills/xiaolujing-review`

确认 `SKILL.md` 直接位于该文件夹中，不要多套一层同名目录。若设置了自定义 `CODEX_HOME`，使用其中的 `skills` 目录。

### 使用 Git 下载

Windows PowerShell：

```powershell
git clone https://github.com/yuhh2026/xiaolujing-review.git "$env:USERPROFILE/.codex/skills/xiaolujing-review"
```

macOS / Linux：

```bash
git clone https://github.com/yuhh2026/xiaolujing-review.git ~/.codex/skills/xiaolujing-review
```

目标文件夹已经存在时，先比较已有版本，不要直接覆盖本地修改。

## 使用方式

向助手提供两份 PDF 的文件或可访问路径，然后发送：

> 使用 $xiaolujing-review 对照英文原文审核这份小绿鲸译文，直接修正已确认错误，保留原格式。原文自身的疑点另记。

助手负责语义审核，脚本负责确定性编辑和验证。脚本本身不会调用翻译 API，也不会自动判断一篇论文是否翻译正确。

默认保留备份、不额外高亮，交付校译 PDF、修改清单和原文疑点。只有用户要求写回原文件时，才在验证通过后备份并写回。

## Python 依赖与脚本

建议 Python 3.12。可使用宿主已有运行环境，无需重复安装。以下依赖版本已在实际 PDF 上验证：

```bash
python -m pip install -r requirements.txt
```

```bash
# 缓存每页文本与字体信息，后续按需读取
python scripts/review_pdf.py inspect --pdf translation.pdf --work work

# 依据经过审核的JSON清单进行原位替换
python scripts/review_pdf.py apply --pdf translation.pdf --manifest changes.json --output corrected.pdf --work work

# 验证页面尺寸、图像、矢量和未改页，并生成修改页预览
python scripts/review_pdf.py verify --before translation.pdf --after corrected.pdf --changes work/translation_changes.json --work work/verify
```

修改清单格式及编辑边界见 [references/pdf-editing.md](references/pdf-editing.md)。清单中的 `source_sha256` 必须是原译文的真实 SHA256；`page` 对应中文 PDF，`basis` 记录英文依据。可用以下命令获取哈希：

```bash
python -c "from pathlib import Path; import hashlib; print(hashlib.sha256(Path('translation.pdf').read_bytes()).hexdigest())"
```

## 能力边界

- 快捷编辑器针对一部分可编辑、CID对应Unicode、等字符数且字槽宽度一致的PDF文字。不支持扫描件、所有复杂字体或任意长度修改；遇到不支持的输入会拒绝输出，不伪装为已完成。
- 不可为了通过等长检查而删改原意。复杂修改仍需要助手单页试验；不能在原区域容纳时留待处理。
- 字体子集可能有映射却没有真实字形。优先复用原字形；必要补字只供替换文字使用，且要确认字体家族和字重。仓库不包含字体文件，同源补字也不能保证与原字库逐字完全一致。
- 英文原文本身的矛盾与中文翻译错误分开记录。变量、模型、数值及因果结论不得凭常见做法补齐。
- 自动验证不能替代修改处的视觉检查或学术语义审核。

缓存和脚本能减少重复提取、重复编程与上下文消耗，不能保证所有论文的处理耗时或 token 消耗相同。

## 仓库内容

```text
SKILL.md                  技能入口
agents/openai.yaml        技能展示信息
references/pdf-editing.md 清单格式、编辑边界与字体处理
scripts/review_pdf.py     提取、应用修改和验证入口
scripts/content_patch.py  复用原字体的内容流编辑器
requirements.txt         已验证的依赖版本
```

仓库不包含论文原文、译文、个人学习记录、访问凭据或字体二进制。第三方依赖遵循各自许可证；本仓库尚未指定独立的开源许可证。
