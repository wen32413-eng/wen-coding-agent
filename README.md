\# Mini Coding Agent



一个从零开始实现的轻量级编程智能体（Coding Agent）运行框架。



该智能体通过大语言模型原生的工具调用（Tool Calling）机制与模型交互，能够自主检查源代码文件、修改代码、执行本地开发命令、观察执行结果，并持续迭代，直到完成用户指定的编程任务。



\## 功能特性



\* 自行实现的 Agent Loop（智能体循环）

\* 原生 LLM Tool Calling 集成

\* 本地文件列表查看与读取

\* 文件创建与修改

\* 本地测试与开发命令执行

\* 工作区路径隔离

\* 上下文历史管理

\* 最大执行步数终止控制

\* 重复工具调用检测

\* 工具错误恢复

\* 命令白名单与执行超时控制



本项目不使用 LangChain、AutoGen、OpenAI Agents SDK、Claude Agent SDK、CrewAI 或其他 Agent 框架。



\## 系统架构



```text

用户任务

&#x20;  |

&#x20;  v

CodingAgent

&#x20;  |

&#x20;  +---- ContextManager

&#x20;  |

&#x20;  v

大语言模型（LLM）

&#x20;  |

&#x20;  v

工具调用（Tool Call）

&#x20;  |

&#x20;  v

工具路由器（Tool Router）

&#x20;  |

&#x20;  +---- list\_files

&#x20;  +---- read\_file

&#x20;  +---- write\_file

&#x20;  +---- replace\_in\_file

&#x20;  +---- run\_command

&#x20;  |

&#x20;  v

本地工作区（Local Workspace）

&#x20;  |

&#x20;  v

工具执行结果 / 观察结果（Observation）

&#x20;  |

&#x20;  +--------------------> LLM

```



\## 环境要求



\* Python 3.10+

\* 支持 OpenAI 兼容 Tool Calling 接口的 LLM API



安装依赖：



```bash

pip install -r requirements.txt

```



\## 配置



配置以下环境变量：



```text

LLM\_API\_KEY

LLM\_BASE\_URL

LLM\_MODEL

```



可选配置：



```text

MAX\_STEPS=20

MAX\_CONTEXT\_STEPS=8

COMMAND\_TIMEOUT=30

```



请勿将 API Key 保存到代码仓库中。



\## 使用方法



将希望智能体修改的项目放入：



```text

workspace/

```



然后运行：



```bash

python main.py

```



输入一个编程任务，例如：



```text

检查当前项目，找出导致测试失败的根本原因，

进行尽可能小的修改，并运行完整的 pytest 测试套件，确认所有测试均通过。

```



智能体将自主检查项目、调用本地工具、修改代码、执行测试，并根据观察到的执行结果继续后续操作。



\## 示例项目



项目在以下目录提供了一个订单处理示例项目：



```text

examples/order\_service\_demo/

```



如需复现演示，可以将示例文件复制到 workspace 目录，然后运行智能体。



PowerShell：



```powershell

Copy-Item -Recurse -Force examples\\order\_service\_demo\\\* workspace\\

python main.py

```



建议使用的任务：



```text

检查当前项目，找出导致测试失败的根本原因，

进行尽可能小的修改，并运行完整的 pytest 测试套件，确认所有测试均通过。

```



\## 安全设计



所有文件操作均被限制在配置好的 workspace 工作区目录中。



开发命令通过可执行程序白名单、超时控制以及 `shell=False` 的方式执行。



本项目并不提供操作系统级别的沙箱隔离。若用于生产环境，还应额外使用容器或其他更强的隔离机制。



\## 当前局限



当前实现是一个轻量级的单智能体 Coding Agent Harness。



目前尚未提供：



\* 语义级代码索引

\* 完整的仓库级代码搜索

\* 操作系统级沙箱隔离

\* 多智能体协作编排

\* 长期持久化记忆



这些限制是有意保留的，目的是让核心 Agent Harness 保持简单、透明，并确保关键机制均由项目独立实现。



