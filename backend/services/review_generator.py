"""
文献综述生成服务
使用 DeepSeek API
"""
import os
from openai import AsyncOpenAI
from typing import List, Dict


class ReviewGeneratorService:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

    async def generate_review(
        self,
        topic: str,
        papers: List[Dict],
        model: str = "deepseek-chat"
    ) -> str:
        """
        生成文献综述

        Args:
            topic: 论文主题
            papers: 文献列表
            model: 模型名称

        Returns:
            Markdown 格式的综述
        """
        # 构建文献引用信息
        papers_info = self._format_papers_for_prompt(papers)

        # 构建提示词
        system_prompt = """你是一位学术写作专家，擅长撰写高质量的文献综述。

请根据提供的文献列表，撰写一篇结构完整、内容深入的文献综述。

综述结构要求：
1. 引言（介绍研究背景和意义）
2. 主体部分（按主题或时间线组织，分析研究进展）
3. 结论（总结现有研究的不足和未来方向）

写作要求（重要）：
- 使用学术化语言
- 每个重要观点、研究结论或数据引用，都必须在句末添加对应的参考文献序号
- 引用格式：[序号]，例如，"这一观点得到了多项研究的支持[1][2][3]"
- 确保正文中至少引用 5 篇不同的文献，不要只引用同一篇
- 分析要深入，不能简单罗列
- 字数：2000-3000字

输出格式：Markdown
注意：不要在输出中包含"参考文献"部分或参考文献列表，只需输出正文内容。"""

        user_prompt = f"""请撰写关于"{topic}"的文献综述。

参考文献列表（共{len(papers)}篇）：
{papers_info}

请开始撰写综述："""

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )

            content = response.choices[0].message.content

            # 移除 AI 可能已经生成的参考文献部分
            content = self._remove_existing_references(content)

            # 附加参考文献列表
            references = self._format_references(papers)
            full_review = f"{content}\n\n## 参考文献\n\n{references}"

            return full_review

        except Exception as e:
            print(f"DeepSeek API error: {e}")
            return self._generate_fallback_review(topic, papers)

    def _format_papers_for_prompt(self, papers: List[Dict]) -> str:
        """格式化论文信息用于 Prompt"""
        formatted = []
        for i, paper in enumerate(papers, 1):
            authors = ", ".join(paper.get("authors", [])[:3])
            if len(paper.get("authors", [])) > 3:
                authors += " 等"

            formatted.append(
                f"[{i}] {paper.get('title', '')}\n"
                f"    作者：{authors}\n"
                f"    年份：{paper.get('year', '')}\n"
                f"    被引量：{paper.get('cited_by_count', 0)}\n"
                f"    摘要：{paper.get('abstract', '')[:200]}..."
            )
        return "\n\n".join(formatted)

    def _format_references(self, papers: List[Dict]) -> str:
        """格式化参考文献列表"""
        references = []
        for i, paper in enumerate(papers, 1):
            authors = ", ".join(paper.get("authors", [])[:3])
            if len(paper.get("authors", [])) > 3:
                authors += " 等"

            doi = paper.get("doi", "")
            doi_suffix = f" DOI: {doi}" if doi else ""

            ref = f"[{i}] {authors}. {paper.get('title', '')}. {paper.get('year', '')}.{doi_suffix}"
            references.append(ref)
        return "\n\n".join(references)

    def _remove_existing_references(self, content: str) -> str:
        """移除 AI 可能已经生成的参考文献部分"""
        lines = content.split('\n')
        result = []

        # 查找参考文献标题的位置
        ref_section_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('## 参考文献') or line.strip().startswith('### 参考文献') or line.strip().startswith('# 参考文献'):
                ref_section_start = i
                break

        if ref_section_start == -1:
            return content  # 没有找到参考文献部分，返回原内容

        # 返回参考文献部分之前的内容
        return '\n'.join(lines[:ref_section_start]).strip()

    def _generate_fallback_review(self, topic: str, papers: List[Dict]) -> str:
        """生成备用综述（当 API 调用失败时）"""
        references = self._format_references(papers)
        return f"""# {topic} 文献综述

## 引言

本文综述了关于"{topic}"的相关研究进展，共收集分析了{len(papers)}篇文献。

## 主要研究内容

根据收集的文献，该领域的主要研究方向包括：

1. 理论基础研究
2. 方法论探讨
3. 实证分析
4. 应用研究

## 结论

（注：由于生成服务暂时不可用，以上为框架内容。请查看下方参考文献获取详细信息。）

## 参考文献

{references}
"""

    async def close(self):
        await self.client.close()
