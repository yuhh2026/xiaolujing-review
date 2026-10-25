# С�̾������������ �� xiaolujing-review

���� Codex �����Ķ���У�뼼�ܣ��ṩӢ��ԭ�ĺ�С�̾����ɵ����� PDF�������ֶ�����ˣ��ٽ���ȷ�ϵĴ���ԭλ������

**����ԭ��ʽ����**������ԭ��ҳ��˫���������ֺš���ʽ��ͼ�����֡��޷���ȫ�Ż�ԭλ�õ��޸ļ�¼Ϊ�����������Զ������塢���ֻ������Ű档

����ĿΪ��������������С�̾��ٷ���������ϵ��

## �����밲װ

### ֱ������

[���� ZIP](https://github.com/yuhh2026/xiaolujing-review/archive/refs/heads/main.zip)����ѹ���ļ�������Ϊ `xiaolujing-review`��������˼���Ŀ¼��

- Windows��`%USERPROFILE%\.codex\skills\xiaolujing-review`
- macOS / Linux��`~/.codex/skills/xiaolujing-review`

ȷ�� `SKILL.md` ֱ��λ�ڸ��ļ����У���Ҫ����һ��ͬ��Ŀ¼�����������Զ��� `CODEX_HOME`��ʹ�����е� `skills` Ŀ¼��

### ʹ�� Git ����

Windows PowerShell��

```powershell
git clone https://github.com/yuhh2026/xiaolujing-review.git "$env:USERPROFILE/.codex/skills/xiaolujing-review"
```

macOS / Linux��

```bash
git clone https://github.com/yuhh2026/xiaolujing-review.git ~/.codex/skills/xiaolujing-review
```

Ŀ���ļ����Ѿ�����ʱ���ȱȽ����а汾����Ҫֱ�Ӹ��Ǳ����޸ġ�

## ʹ�÷�ʽ

�������ṩ���� PDF ���ļ���ɷ���·����Ȼ���ͣ�

> ʹ�� $xiaolujing-review ����Ӣ��ԭ��������С�̾����ģ�ֱ��������ȷ�ϴ��󣬱���ԭ��ʽ��ԭ���������ɵ����ǡ�

���ָ���������ˣ��ű�����ȷ���Ա༭����֤���ű�����������÷��� API��Ҳ�����Զ��ж�һƪ�����Ƿ�����ȷ��

Ĭ�ϱ������ݡ����������������У�� PDF���޸��嵥��ԭ���ɵ㡣ֻ���û�Ҫ��д��ԭ�ļ�ʱ��������֤ͨ���󱸷ݲ�д�ء�

## Python ������ű�

���� Python 3.12����ʹ�������������л����������ظ���װ�����������汾����ʵ�� PDF ����֤��

```bash
python -m pip install -r requirements.txt
```

```bash
# ����ÿҳ�ı���������Ϣ�����������ȡ
python scripts/review_pdf.py inspect --pdf translation.pdf --work work

# ���ݾ�����˵�JSON�嵥����ԭλ�滻
python scripts/review_pdf.py apply --pdf translation.pdf --manifest changes.json --output corrected.pdf --work work

# ��֤ҳ��ߴ硢ͼ��ʸ����δ��ҳ���������޸�ҳԤ��
python scripts/review_pdf.py verify --before translation.pdf --after corrected.pdf --changes work/translation_changes.json --work work/verify
```

�޸��嵥��ʽ���༭�߽�� [references/pdf-editing.md](references/pdf-editing.md)���嵥�е� `source_sha256` ������ԭ���ĵ���ʵ SHA256��`page` ��Ӧ���� PDF��`basis` ��¼Ӣ�����ݡ��������������ȡ��ϣ��

```bash
python -c "from pathlib import Path; import hashlib; print(hashlib.sha256(Path('translation.pdf').read_bytes()).hexdigest())"
```

## �����߽�

- ��ݱ༭�����һ���ֿɱ༭��CID��ӦUnicode�����ַ������ֲۿ���һ�µ�PDF���֡���֧��ɨ��������и�����������ⳤ���޸ģ�������֧�ֵ������ܾ��������αװΪ����ɡ�
- ����Ϊ��ͨ���ȳ�����ɾ��ԭ�⡣�����޸�����Ҫ���ֵ�ҳ���飻������ԭ��������ʱ����������
- �����Ӽ�������ӳ��ȴû����ʵ���Ρ����ȸ���ԭ���Σ���Ҫ����ֻ���滻����ʹ�ã���Ҫȷ�������������ء��ֿⲻ���������ļ���ͬԴ����Ҳ���ܱ�֤��ԭ�ֿ�������ȫһ�¡�
- Ӣ��ԭ�ı�����ì�������ķ������ֿ���¼��������ģ�͡���ֵ��������۲���ƾ�����������롣
- �Զ���֤��������޸Ĵ����Ӿ�����ѧ��������ˡ�

����ͽű��ܼ����ظ���ȡ���ظ���������������ģ����ܱ�֤�������ĵĴ�����ʱ�� token ������ͬ��

## �ֿ�����

```text
SKILL.md                  �������
agents/openai.yaml        ����չʾ��Ϣ
references/pdf-editing.md �嵥��ʽ���༭�߽������崦��
scripts/review_pdf.py     ��ȡ��Ӧ���޸ĺ���֤���
scripts/content_patch.py  ����ԭ������������༭��
requirements.txt         ����֤�������汾
```

�ֿⲻ��������ԭ�ġ����ġ�����ѧϰ��¼������ƾ�ݻ���������ơ�������������ѭ��������֤�����ֿ���δָ�������Ŀ�Դ����֤��
