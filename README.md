# yande-crawler

本程序的设计目的是从 yande.re 上爬取图片。
## 配置文件 config.json
|         参数         | 类型 |     解释      |     默认     |
| -------------------- | ---- | ------------- | ------------ |
| start                | 必选 | 起始页码      |              |
| end                  | 必选 | 结束页码      |              |
| save_dir             | 必选 | 保存路径      |              |
| thread_num           | 可选 | 线程数        | 单线程       |
| log                  | 可选 | 日志位置      | 不记录日志   |
| log_autopurge        | 可选 | 自动清空日志  | 不清空日志   |
| tags                 | 可选 | 标签          | 处理全部图片 |
| except_tags          | 可选 | 排除标签      | 不排除图片   |
| no_check_certificate | 可选 | 不检查SSL证书 | 检查SSL证书  |
| proxy                | 可选 | 使用代理      | 不使用代理   |
| proxy_addr           | 可选 | 代理地址      | 不使用代理   |
