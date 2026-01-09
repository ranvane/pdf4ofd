

# 📄 pdf4ofd

一个基于 [easyofd v0.5.1](https://github.com/renoyuan/easyofd) 实现的轻量级工具，用于 **PDF 与 OFD 文件之间的相互转换**。

  OFD（Open Fixed-layout Document）是中国自主制定的版式文档格式标准，广泛应用于电子发票、公文等领域。本工具旨在简化 OFD 与 PDF 格式间的互操作流程。

---

## 🔧 功能特性

- ✅ PDF → OFD 转换  
- ✅ OFD → PDF 转换  
- ⚙️ 基于纯 Python 实现，无需依赖外部服务  
- 📦 简单易用。

---

## ⚠️ 重要说明

本项目 **并非直接完全使用 `easyofd v0.5.1` 的原始代码**，而是对其进行了部分修改以适配实际运行需求。

**原因说明 **： 

  在使用 `easyofd v0.5.1` 原版时，我遇到了若干运行问题。这些问题**可能源于库本身的限制，也可能源于我的使用方式**。为确保功能可用，我们对底层代码做了针对性调整。

📌 **请勿将本项目与 `easyofd v0.5.1` 官方版本直接对比或混用**。建议在使用前自行测试转换效果。


---

## 📦 依赖项目

- [easyofd](https://github.com/renoyuan/easyofd) by [@renoyuan](https://github.com/renoyuan)  
  > 若本工具对你有帮助，也欢迎为原项目点个 ⭐！

---



> 💡 **提示**：OFD 格式仍在演进中，不同厂商生成的 OFD 文件可能存在兼容性差异。建议在生产环境中充分验证转换结果。