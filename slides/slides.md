---
theme: apple-basic
title: 10分钟出完整文献综述 + 对比矩阵
info: |
  Danmo Scholar — 研究生毕业论文救命神器
  网页端 AI 文献助手
class: text-center
drawings:
  persist: false
transition: slide-left
mdc: true
---

# 10分钟出完整文献综述 + 对比矩阵！

研究生毕业论文救命神器（真实案例）

<div class="pt-12">
  <span @click="$slidev.nav.next" class="px-2 py-1 rounded cursor-pointer" hover="bg-white bg-opacity-10">
    Press Space for next page <carbon:arrow-right class="inline"/>
  </span>
</div>

<div class="abs-br m-6 flex gap-2">
  <a href="https://danmo.tech" target="_blank" alt="Danmo Scholar"
    class="text-xl slidev-icon-btn opacity-50 !border-none !hover:text-white">
    Danmo Scholar
  </a>
</div>

---
layout: center
class: text-center
---

# 写文献综述，是不是快把你逼疯了？

<div class="text-2xl text-gray-400 mt-8">
  <p>手动查几百篇论文</p>
  <p>做 Excel 对比矩阵</p>
  <p class="text-red-400">ChatGPT 一用就整出假引用、假 DOI</p>
</div>

<div class="text-lg text-gray-500 mt-12">
  导师看了直接说："这能发吗？"
</div>

---
layout: center
---

# 文献综述的 3 大痛点

<div class="grid grid-cols-3 gap-8 mt-12">
  <div class="border rounded-lg p-6 text-center">
    <div class="text-5xl mb-4">🔍</div>
    <h3>手动查找太慢</h3>
    <p class="text-sm text-gray-400 mt-2">几百篇论文逐个搜索筛选</p>
  </div>
  <div class="border rounded-lg p-6 text-center">
    <div class="text-5xl mb-4">📊</div>
    <h3>对比矩阵极痛苦</h3>
    <p class="text-sm text-gray-400 mt-2">Excel 一行一行手动填写</p>
  </div>
  <div class="border rounded-lg p-6 text-center">
    <div class="text-5xl mb-4">⚠️</div>
    <h3>AI 假引用风险高</h3>
    <p class="text-sm text-gray-400 mt-2">虚假 DOI 直接被导师打回</p>
  </div>
</div>

---
layout: two-cols
---

# 传统做法 <span class="text-red-500">❌</span>

<div class="mt-8 space-y-4 text-gray-400">
  <p>❌ 手动搜几百篇论文</p>
  <p>❌ Excel 手动做矩阵</p>
  <p>❌ 熬夜整理格式</p>
  <p>❌ 容易出现假引用</p>
</div>

::right::

# Danmo Scholar <span class="text-green-500">✅</span>

<div class="mt-8 space-y-4 text-green-400">
  <p>✅ 输入主题即可</p>
  <p>✅ 10 分钟自动生成</p>
  <p>✅ 完整综述 + 对比矩阵 + 海报</p>
  <p>✅ 真实 DOI 双重验证</p>
</div>

---
layout: center
class: text-center
---

# Danmo Scholar 能一次性输出什么？

<div class="grid grid-cols-2 gap-6 mt-12">
  <div class="border rounded-lg p-8">
    <div class="text-4xl mb-3">📝</div>
    <h3 class="text-lg">完整学术文献综述</h3>
    <p class="text-sm text-gray-400 mt-2">规范引用格式</p>
  </div>
  <div class="border rounded-lg p-8">
    <div class="text-4xl mb-3">📊</div>
    <h3 class="text-lg">文献对比矩阵</h3>
    <p class="text-sm text-gray-400 mt-2">方法 / 结果 / 结论</p>
  </div>
  <div class="border rounded-lg p-8">
    <div class="text-4xl mb-3">🎨</div>
    <h3 class="text-lg">专业分享海报</h3>
    <p class="text-sm text-gray-400 mt-2">直接可发小红书</p>
  </div>
  <div class="border rounded-lg p-8">
    <div class="text-4xl mb-3">✅</div>
    <h3 class="text-lg">真实 DOI 验证</h3>
    <p class="text-sm text-gray-400 mt-2">Crossref + 百度学术</p>
  </div>
</div>

---
layout: center
---

# 实际操作演示（全流程）

<div class="mt-12 space-y-8">
  <div class="flex items-center gap-4">
    <span class="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold shrink-0">1</span>
    <div>
      <h3>输入研究主题</h3>
      <p class="text-sm text-gray-400">例如："脑机接口在中风康复中的研究进展"</p>
    </div>
  </div>
  <div class="flex items-center gap-4">
    <span class="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold shrink-0">2</span>
    <div>
      <h3>AI 自动搜索 + 提取信息</h3>
      <p class="text-sm text-gray-400">从 OpenAlex、Semantic Scholar 等数据库检索</p>
    </div>
  </div>
  <div class="flex items-center gap-4">
    <span class="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold shrink-0">3</span>
    <div>
      <h3>生成对比矩阵</h3>
      <p class="text-sm text-gray-400">自动整理方法、结果、结论对比</p>
    </div>
  </div>
  <div class="flex items-center gap-4">
    <span class="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold shrink-0">4</span>
    <div>
      <h3>输出完整综述 + 海报</h3>
      <p class="text-sm text-gray-400">支持 Markdown / Word / PDF 导出</p>
    </div>
  </div>
</div>

---
layout: center
class: text-center
---

# 真实案例 1：脑机接口在中风康复

<div class="mt-8">
  <span class="text-6xl font-bold text-blue-400">42</span>
  <span class="text-2xl text-gray-400 ml-2">篇文献</span>
</div>

<p class="text-gray-400 mt-4">生成时间：2026 年 4 月</p>

<div class="mt-8 text-gray-500 text-sm">
  海报、对比矩阵、完整综述 一键生成
</div>

---
layout: center
class: text-center
---

# 真实案例 2 & 3

<div class="grid grid-cols-2 gap-12 mt-12">
  <div class="border rounded-lg p-8">
    <h3 class="text-lg mb-4">案例 2</h3>
    <p class="text-gray-400">AI 满足老年人情感需求的研究</p>
    <p class="text-blue-400 text-3xl font-bold mt-4">28 篇文献</p>
  </div>
  <div class="border rounded-lg p-8">
    <h3 class="text-lg mb-4">案例 3</h3>
    <p class="text-gray-400">智能优化算法求解电路方程对比研究</p>
    <p class="text-blue-400 text-3xl font-bold mt-4">3 个表格</p>
  </div>
</div>

---
layout: center
---

# 核心价值总结

<div class="mt-12 space-y-6">
  <div class="flex items-center gap-4">
    <span class="text-3xl">⏱</span>
    <div>
      <h3 class="text-lg">节省 10-20 小时手动工作</h3>
    </div>
  </div>
  <div class="flex items-center gap-4">
    <span class="text-3xl">🛡</span>
    <div>
      <h3 class="text-lg">杜绝假引用和无效 DOI</h3>
    </div>
  </div>
  <div class="flex items-center gap-4">
    <span class="text-3xl">📄</span>
    <div>
      <h3 class="text-lg">输出可直接用于毕业论文 / 开题报告</h3>
    </div>
  </div>
  <div class="flex items-center gap-4">
    <span class="text-3xl">🎨</span>
    <div>
      <h3 class="text-lg">专业海报方便发小红书 / 朋友圈</h3>
    </div>
  </div>
</div>

---
layout: center
class: text-center
---

# 免费试用

<div class="mt-12 space-y-6">
  <p class="text-2xl">评论区打 <span class="text-blue-400 font-bold">「综述」</span> 两个字</p>
  <p class="text-gray-400">我看到就会私信你免费体验链接</p>
</div>

<div class="mt-16">
  <p class="text-gray-500">官网</p>
  <p class="text-2xl font-bold mt-2">danmo.tech</p>
</div>

<div class="mt-12 text-gray-500 text-sm">
  点赞 · 投币 · 关注 — 下期见！
</div>
